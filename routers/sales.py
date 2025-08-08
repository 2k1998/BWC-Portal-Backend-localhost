# routers/sales.py - Sales and Commission management API
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, or_, and_, func, extract
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json

from database import get_db
import models, schemas
from .auth import get_current_user
from .utils import check_roles

router = APIRouter(prefix="/sales", tags=["sales"])

# ==================== SALES ENDPOINTS ====================

@router.post("/", response_model=schemas.SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: schemas.SaleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new sale"""
    check_roles(current_user, ["admin", "Manager", "Head", "Pillar"])
    
    # Verify salesperson exists
    salesperson = db.query(models.User).filter(models.User.id == sale.salesperson_id).first()
    if not salesperson:
        raise HTTPException(status_code=404, detail="Salesperson not found")
    
    # Create new sale
    db_sale = models.Sale(
        **sale.model_dump(),
        created_by_id=current_user.id
    )
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Load relationships for response
    db_sale = db.query(models.Sale).options(
        joinedload(models.Sale.salesperson),
        joinedload(models.Sale.company),
        joinedload(models.Sale.created_by)
    ).filter(models.Sale.id == sale_id).first()
    
    return db_sale

@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a sale"""
    check_roles(current_user, ["admin"])
    
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    db.delete(db_sale)
    db.commit()
    
    return None

# ==================== COMMISSION RULES ENDPOINTS ====================

@router.post("/commission-rules", response_model=schemas.CommissionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_commission_rule(
    rule: schemas.CommissionRuleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a commission rule for an employee"""
    check_roles(current_user, ["admin", "Manager", "Head"])
    
    # Verify employee exists
    employee = db.query(models.User).filter(models.User.id == rule.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create new rule
    db_rule = models.EmployeeCommissionRule(
        **rule.model_dump(),
        created_by_id=current_user.id
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    # Load relationships for response
    db_rule = db.query(models.EmployeeCommissionRule).options(
        joinedload(models.EmployeeCommissionRule.employee),
        joinedload(models.EmployeeCommissionRule.created_by)
    ).filter(models.EmployeeCommissionRule.id == db_rule.id).first()
    
    return db_rule

@router.get("/commission-rules", response_model=List[schemas.CommissionRuleResponse])
async def get_commission_rules(
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get commission rules"""
    check_roles(current_user, ["admin", "Manager", "Head"])
    
    query = db.query(models.EmployeeCommissionRule).options(
        joinedload(models.EmployeeCommissionRule.employee),
        joinedload(models.EmployeeCommissionRule.created_by)
    )
    
    if employee_id:
        query = query.filter(models.EmployeeCommissionRule.employee_id == employee_id)
    
    return query.filter(models.EmployeeCommissionRule.is_active == True).all()

# ==================== COMMISSION CALCULATION ENDPOINTS ====================

@router.post("/calculate-commission", response_model=schemas.CommissionSummaryResponse)
async def calculate_monthly_commission(
    calculation_request: schemas.CommissionCalculationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate monthly commission for an employee"""
    check_roles(current_user, ["admin", "Manager", "Head"])
    
    employee_id = calculation_request.employee_id
    year = calculation_request.year
    month = calculation_request.month
    
    # Verify employee exists
    employee = db.query(models.User).filter(models.User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if summary already exists
    existing_summary = db.query(models.MonthlyCommissionSummary).filter(
        models.MonthlyCommissionSummary.employee_id == employee_id,
        models.MonthlyCommissionSummary.year == year,
        models.MonthlyCommissionSummary.month == month
    ).first()
    
    if existing_summary and not calculation_request.recalculate:
        # Load relationships for response
        existing_summary = db.query(models.MonthlyCommissionSummary).options(
            joinedload(models.MonthlyCommissionSummary.employee),
            joinedload(models.MonthlyCommissionSummary.calculated_by)
        ).filter(models.MonthlyCommissionSummary.id == existing_summary.id).first()
        return existing_summary
    
    # Get commission rules for this employee
    commission_rules = db.query(models.EmployeeCommissionRule).filter(
        models.EmployeeCommissionRule.employee_id == employee_id,
        models.EmployeeCommissionRule.is_active == True
    ).all()
    
    if not commission_rules:
        raise HTTPException(status_code=400, detail="No commission rules found for this employee")
    
    # Calculate date range for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - relativedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - relativedelta(days=1)
    
    # Get closed sales for this employee in the specified month
    closed_sales = db.query(models.Sale).filter(
        models.Sale.salesperson_id == employee_id,
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= start_date,
        models.Sale.close_date <= end_date
    ).all()
    
    # Get active leads count
    active_leads = db.query(models.Sale).filter(
        models.Sale.salesperson_id == employee_id,
        models.Sale.status.in_([
            models.SaleStatus.lead,
            models.SaleStatus.proposal_sent,
            models.SaleStatus.negotiating
        ])
    ).count()
    
    # Calculate totals
    total_sales_amount = sum(sale.sale_amount for sale in closed_sales)
    closed_deals_count = len(closed_sales)
    
    # Calculate base commission
    base_commission = 0
    sales_breakdown = {}
    
    for sale in closed_sales:
        # Find applicable commission rule
        applicable_rule = None
        for rule in commission_rules:
            if rule.sale_type is None or rule.sale_type == sale.sale_type:
                if sale.sale_amount >= rule.min_sale_amount:
                    applicable_rule = rule
                    break
        
        if applicable_rule:
            commission = (sale.sale_amount * applicable_rule.base_commission_rate) / 100
            base_commission += commission
            
            # Update sale with calculated commission
            sale.commission_amount = commission
            sale.commission_status = models.CommissionStatus.calculated
            
            # Track breakdown by sale type
            sale_type_key = sale.sale_type.value
            if sale_type_key not in sales_breakdown:
                sales_breakdown[sale_type_key] = {
                    'count': 0,
                    'total_amount': 0,
                    'commission': 0
                }
            sales_breakdown[sale_type_key]['count'] += 1
            sales_breakdown[sale_type_key]['total_amount'] += float(sale.sale_amount)
            sales_breakdown[sale_type_key]['commission'] += float(commission)
    
    # Calculate tier bonuses
    tier_bonus = 0
    for rule in commission_rules:
        if rule.tier1_threshold and total_sales_amount >= rule.tier1_threshold:
            tier_bonus += (total_sales_amount * rule.tier1_bonus_rate) / 100
        if rule.tier2_threshold and total_sales_amount >= rule.tier2_threshold:
            tier_bonus += (total_sales_amount * rule.tier2_bonus_rate) / 100
        if rule.tier3_threshold and total_sales_amount >= rule.tier3_threshold:
            tier_bonus += (total_sales_amount * rule.tier3_bonus_rate) / 100
    
    total_commission = base_commission + tier_bonus
    
    # Create or update commission summary
    if existing_summary:
        summary = existing_summary
    else:
        summary = models.MonthlyCommissionSummary(
            employee_id=employee_id,
            year=year,
            month=month,
            calculated_by_id=current_user.id
        )
        db.add(summary)
    
    # Update summary data
    summary.total_sales_amount = total_sales_amount
    summary.closed_deals_count = closed_deals_count
    summary.active_leads_count = active_leads
    summary.base_commission = base_commission
    summary.tier_bonus = tier_bonus
    summary.total_commission = total_commission
    summary.sales_breakdown = json.dumps(sales_breakdown)
    summary.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(summary)
    
    # Load relationships for response
    summary = db.query(models.MonthlyCommissionSummary).options(
        joinedload(models.MonthlyCommissionSummary.employee),
        joinedload(models.MonthlyCommissionSummary.calculated_by)
    ).filter(models.MonthlyCommissionSummary.id == summary.id).first()
    
    return summary

@router.get("/commission-summaries", response_model=List[schemas.CommissionSummaryResponse])
async def get_commission_summaries(
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get commission summaries with filtering"""
    check_roles(current_user, ["admin", "Manager", "Head"])
    
    query = db.query(models.MonthlyCommissionSummary).options(
        joinedload(models.MonthlyCommissionSummary.employee),
        joinedload(models.MonthlyCommissionSummary.calculated_by)
    )
    
    if employee_id:
        query = query.filter(models.MonthlyCommissionSummary.employee_id == employee_id)
    
    if year:
        query = query.filter(models.MonthlyCommissionSummary.year == year)
    
    if month:
        query = query.filter(models.MonthlyCommissionSummary.month == month)
    
    return query.order_by(
        desc(models.MonthlyCommissionSummary.year),
        desc(models.MonthlyCommissionSummary.month)
    ).all()

# ==================== DASHBOARD/STATS ENDPOINTS ====================

@router.get("/stats/dashboard", response_model=schemas.SalesDashboardSummary)
async def get_sales_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get sales dashboard statistics"""
    
    current_date = datetime.now().date()
    current_month_start = date(current_date.year, current_date.month, 1)
    if current_date.month == 1:
        previous_month_start = date(current_date.year - 1, 12, 1)
        previous_month_end = date(current_date.year, 1, 1) - relativedelta(days=1)
    else:
        previous_month_start = date(current_date.year, current_date.month - 1, 1)
        previous_month_end = date(current_date.year, current_date.month, 1) - relativedelta(days=1)
    
    # Current month stats
    current_month_sales = db.query(func.coalesce(func.sum(models.Sale.sale_amount), 0)).filter(
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= current_month_start,
        models.Sale.close_date <= current_date
    ).scalar()
    
    current_month_deals = db.query(models.Sale).filter(
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= current_month_start,
        models.Sale.close_date <= current_date
    ).count()
    
    # Previous month stats
    previous_month_sales = db.query(func.coalesce(func.sum(models.Sale.sale_amount), 0)).filter(
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= previous_month_start,
        models.Sale.close_date <= previous_month_end
    ).scalar()
    
    previous_month_deals = db.query(models.Sale).filter(
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= previous_month_start,
        models.Sale.close_date <= previous_month_end
    ).count()
    
    # Calculate growth
    sales_growth = 0
    if previous_month_sales > 0:
        sales_growth = ((current_month_sales - previous_month_sales) / previous_month_sales) * 100
    
    # Current month commission
    current_month_commission = db.query(func.coalesce(func.sum(models.MonthlyCommissionSummary.total_commission), 0)).filter(
        models.MonthlyCommissionSummary.year == current_date.year,
        models.MonthlyCommissionSummary.month == current_date.month
    ).scalar()
    
    # Pending counts
    pending_leads = db.query(models.Sale).filter(
        models.Sale.status == models.SaleStatus.lead
    ).count()
    
    pending_proposals = db.query(models.Sale).filter(
        models.Sale.status == models.SaleStatus.proposal_sent
    ).count()
    
    pending_commission_payments = db.query(models.Payment).filter(
        models.Payment.payment_type == models.PaymentType.commission_payment,
        models.Payment.status == models.PaymentStatus.pending
    ).count()
    
    overdue_payments = db.query(models.Payment).filter(
        models.Payment.status == models.PaymentStatus.overdue
    ).count()
    
    # Top performer this month
    top_performer = db.query(
        models.User.full_name,
        func.sum(models.Sale.sale_amount).label('total_sales')
    ).join(
        models.Sale, models.User.id == models.Sale.salesperson_id
    ).filter(
        models.Sale.status == models.SaleStatus.closed_won,
        models.Sale.close_date >= current_month_start,
        models.Sale.close_date <= current_date
    ).group_by(
        models.User.id, models.User.full_name
    ).order_by(
        desc('total_sales')
    ).first()
    
    top_salesperson = top_performer[0] if top_performer else "None"
    top_salesperson_amount = top_performer[1] if top_performer else 0
    
    return {
        "current_month_sales": current_month_sales,
        "current_month_deals": current_month_deals,
        "current_month_commission": current_month_commission,
        "previous_month_sales": previous_month_sales,
        "previous_month_deals": previous_month_deals,
        "sales_growth_percentage": round(sales_growth, 2),
        "pending_leads": pending_leads,
        "pending_proposals": pending_proposals,
        "pending_commission_payments": pending_commission_payments,
        "overdue_payments": overdue_payments,
        "top_salesperson": top_salesperson,
        "top_salesperson_amount": top_salesperson_amount
    }

@router.get("/", response_model=List[schemas.SaleListItem])
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[models.SaleStatus] = None,
    sale_type_filter: Optional[models.SaleType] = None,
    salesperson_id: Optional[int] = None,
    company_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(title|sale_amount|lead_date|close_date|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all sales with filtering and sorting"""
    
    query = db.query(models.Sale).options(
        joinedload(models.Sale.salesperson),
        joinedload(models.Sale.company)
    )
    
    # Apply filters
    if status_filter:
        query = query.filter(models.Sale.status == status_filter)
    
    if sale_type_filter:
        query = query.filter(models.Sale.sale_type == sale_type_filter)
    
    if salesperson_id:
        query = query.filter(models.Sale.salesperson_id == salesperson_id)
    
    if company_id:
        query = query.filter(models.Sale.company_id == company_id)
    
    if from_date:
        query = query.filter(models.Sale.lead_date >= from_date)
    
    if to_date:
        query = query.filter(models.Sale.lead_date <= to_date)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Sale.title.ilike(search_term),
                models.Sale.client_name.ilike(search_term),
                models.Sale.client_company.ilike(search_term)
            )
        )
    
    # Apply sorting
    order_func = desc if sort_order == "desc" else asc
    if sort_by == "title":
        query = query.order_by(order_func(models.Sale.title))
    elif sort_by == "sale_amount":
        query = query.order_by(order_func(models.Sale.sale_amount))
    elif sort_by == "lead_date":
        query = query.order_by(order_func(models.Sale.lead_date))
    elif sort_by == "close_date":
        query = query.order_by(order_func(models.Sale.close_date))
    else:  # created_at
        query = query.order_by(order_func(models.Sale.created_at))
    
    sales = query.offset(skip).limit(limit).all()
    
    # Transform to list items
    sale_list = []
    for sale in sales:
        sale_list.append({
            "id": sale.id,
            "title": sale.title,
            "sale_type": sale.sale_type,
            "status": sale.status,
            "sale_amount": sale.sale_amount,
            "currency": sale.currency,
            "client_name": sale.client_name,
            "salesperson_name": sale.salesperson.full_name if sale.salesperson else "Unknown",
            "commission_amount": sale.commission_amount,
            "lead_date": sale.lead_date,
            "close_date": sale.close_date,
            "expected_close_date": sale.expected_close_date,
            "created_at": sale.created_at
        })
    
    return sale_list

@router.get("/{sale_id}", response_model=schemas.SaleResponse)
async def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific sale by ID"""
    
    sale = db.query(models.Sale).options(
        joinedload(models.Sale.salesperson),
        joinedload(models.Sale.company),
        joinedload(models.Sale.created_by)
    ).filter(models.Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    return sale

@router.put("/{sale_id}", response_model=schemas.SaleResponse)
async def update_sale(
    sale_id: int,
    sale_update: schemas.SaleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a sale"""
    check_roles(current_user, ["admin", "Manager", "Head", "Pillar"])
    
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Update fields
    update_data = sale_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    # Recalculate commission if status changed to closed_won
    if sale_update.status == models.SaleStatus.closed_won:
        db_sale.calculate_commission()
    
    db_sale.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_sale)
    
    # Load relationships for response
    db_sale = db.query(models.Sale).options(
        joinedload(models.Sale.salesperson),
        joinedload(models.Sale.company),
        joinedload(models.Sale.created_by)
    ).filter(models.Sale.id == sale_id).first()
    
    return db_sale

@router.patch("/{sale_id}/status", response_model=schemas.SaleResponse)
async def update_sale_status(
    sale_id: int,
    status_update: schemas.SaleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update sale status"""
    check_roles(current_user, ["admin", "Manager", "Head", "Pillar"])
    
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Update status
    db_sale.status = status_update.status
    if status_update.close_date:
        db_sale.close_date = status_update.close_date
    if status_update.notes:
        db_sale.notes = status_update.notes
    
    # Auto-set close date if closing deal
    if status_update.status in [models.SaleStatus.closed_won, models.SaleStatus.closed_lost]:
        if not db_sale.close_date:
            db_sale.close_date = datetime.utcnow().date()
    
    # Calculate commission if deal is won
    if status_update.status == models.SaleStatus.closed_won:
        db_sale.calculate_commission()
    
    db_sale.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_sale)
    
    # Load relationships for response
    db_sale = db.query(models.Sale).options(
        joinedload(models.Sale.salesperson),
        joinedload(models.Sale.company),
        joinedload(models.Sale.created_by)
    ).filter(models.Sale.id == sale_id).first()
    
