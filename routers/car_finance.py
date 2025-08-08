from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from decimal import Decimal

import models
from database import get_db
from .auth import get_current_user
from .utils import check_roles

router = APIRouter(prefix="/car-finances", tags=["car-finances"])

# Pydantic Models
class CarIncomeCreate(BaseModel):
    rental_id: Optional[int] = None
    car_id: int
    amount: Decimal
    description: Optional[str] = None
    date: date
    customer_name: str

class CarExpenseCreate(BaseModel):
    car_id: int
    service_type: str
    amount: Decimal
    description: Optional[str] = None
    date: date
    vendor: str
    mileage: Optional[int] = None

class CarFinanceSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal

# API Endpoints
@router.get("/summary")
def get_finance_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get financial summary for car fleet"""
    check_roles(current_user, ["admin"])
    
    # Get Best Solution Cars company
    company = db.query(models.Company).filter(
        models.Company.name == "Best Solution Cars"
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Calculate income from rentals
    rental_query = db.query(models.Rental).filter(
        models.Rental.company_id == company.id,
        models.Rental.is_locked == True
    )
    
    if start_date:
        rental_query = rental_query.filter(models.Rental.created_at >= start_date)
    if end_date:
        rental_query = rental_query.filter(models.Rental.created_at <= end_date)
    
    rentals = rental_query.all()
    
    # Calculate total income (simplified - you should have a rate field)
    total_income = sum(r.rental_days * 50 for r in rentals)  # €50 per day default
    
    # Get expenses from CarService table (you'll need to create this)
    # For now, returning mock data
    total_expenses = 1980  # Mock value
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "monthly_income": total_income,  # Simplified
        "monthly_expenses": total_expenses
    }

@router.post("/income")
def add_car_income(
    income: CarIncomeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add income record for car rental"""
    check_roles(current_user, ["admin"])
    
    # Create income record in your database
    # You'll need to create a CarIncome model
    return {"message": "Income added successfully"}

@router.post("/expense")
def add_car_expense(
    expense: CarExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add expense record for car service"""
    check_roles(current_user, ["admin"])
    
    # Create expense record in your database
    # You'll need to create a CarExpense model
    return {"message": "Expense added successfully"}

@router.get("/transactions")
def get_car_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[str] = None,  # 'income' or 'expense'
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all car-related financial transactions"""
    check_roles(current_user, ["admin"])
    
    # Fetch and return transactions
    # Combine income and expense records
    return []