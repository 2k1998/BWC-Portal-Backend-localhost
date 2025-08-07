from datetime import datetime, date
from pydantic import BaseModel, EmailStr, ConfigDict, computed_field, validator, Field
from typing import Optional, List
from enum import Enum
from models import GasTankLevel, TaskStatus, ProjectStatus, ProjectType, SaleType, SaleStatus, CommissionStatus, PaymentType, PaymentStatus
from decimal import Decimal

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    surname: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str
    profile_picture_url: Optional[str] = None

    @computed_field
    @property
    def full_name(self) -> str:
        if self.first_name and self.surname:
            return f"{self.first_name} {self.surname}"
        return self.first_name or self.surname or self.email
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    birthday: Optional[date] = None

class UserRoleUpdate(BaseModel):
    role: str

class UserStatusUpdate(BaseModel):
    is_active: bool

# --- Basic Info Schemas (Used to break circular dependencies) ---
class UserBasicInfo(BaseModel):
    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


# --- Task History Schemas (Defined before they are used in TaskResponse) ---
class TaskHistoryBase(BaseModel):
    timestamp: datetime
    status_from: Optional[TaskStatus] = None
    status_to: Optional[TaskStatus] = None
    comment: Optional[str] = None

class TaskHistoryOut(TaskHistoryBase):
    id: int
    changed_by: UserBasicInfo
    model_config = ConfigDict(from_attributes=True)


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[EmailStr] = None


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline_all_day: bool = False
    deadline: Optional[datetime] = None
    urgency: bool = False
    important: bool = False
    company_id: Optional[int] = None
    owner_id: Optional[int] = None
    department: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline_all_day: Optional[bool] = None
    deadline: Optional[datetime] = None
    urgency: Optional[bool] = False
    important: Optional[bool] = False
    status: Optional[TaskStatus] = None
    company_id: Optional[int] = None
    department: Optional[str] = None
    comment: Optional[str] = None

class TaskStatusEnum(str, Enum):
    NEW = "new"
    RECEIVED = "received"
    ON_PROCESS = "on_process"
    PENDING = "pending"
    COMPLETED = "completed"
    LOOSE_END = "loose_end"

class TaskStatusUpdate(BaseModel):
    status: TaskStatusEnum
    status_comments: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_date: Optional[datetime]
    deadline: Optional[datetime]
    deadline_all_day: bool
    urgency: bool
    important: bool
    completed: bool

    # NEW: Status fields
    status: TaskStatusEnum
    status_comments: Optional[str]
    status_updated_at: Optional[datetime]
    status_updated_by: Optional[int]

    owner_id: int
    group_id: Optional[int]
    company_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    # Include related objects
    owner: Optional["UserResponse"]
    status_updater: Optional["UserResponse"]

    class Config:
        from_attributes = True


# --- Group Schemas ---
class GroupCreate(BaseModel):
    name: str

class GroupOut(BaseModel):
    id: int
    name: str
    members: List[UserResponse] = []
    model_config = ConfigDict(from_attributes=True)

# --- THIS CLASS IS NOW RESTORED ---
class GroupTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline_all_day: bool = False
    deadline: Optional[datetime] = None
    urgency: bool = False
    important: bool = False

# --- Other Schemas ---
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class NotificationOut(BaseModel):
    id: int
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Contact Schemas ---
class ContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    notes: Optional[str] = None

    @validator('email', pre=True)
    def blank_string_to_none(cls, v):
        if v == "":
            return None
        return v

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    notes: Optional[str] = None

    @validator('email', pre=True)
    def blank_string_to_none(cls, v):
        if v == "":
            return None
        return v

class ContactOut(ContactBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

class ContactIdList(BaseModel):
    contact_ids: List[int]

class ContactImport(BaseModel):
    contacts: List[ContactCreate]

# --- Daily Call Schemas ---
class DailyCallCreate(BaseModel):
    contact_id: int

class DailyCallUpdate(BaseModel):
    call_frequency_per_day: Optional[int] = None
    next_call_at: Optional[datetime] = None

class DailyCallOut(BaseModel):
    id: int
    user_id: int
    contact_id: int
    call_frequency_per_day: int
    next_call_at: Optional[datetime] = None
    contact: ContactOut 
    model_config = ConfigDict(from_attributes=True)

# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str
    vat_number: Optional[str] = None
    occupation: Optional[str] = None
    creation_date: Optional[date] = None
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    vat_number: Optional[str] = None
    occupation: Optional[str] = None
    creation_date: Optional[date] = None
    description: Optional[str] = None

class CompanyOut(CompanyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Car & Rental Schemas ---
class CarBase(BaseModel):
    manufacturer: str
    model: str
    license_plate: str
    vin: str

class CarCreate(CarBase):
    pass

class CarUpdate(CarBase):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None
    vin: Optional[str] = None

class CarOut(CarBase):
    id: int
    company_id: int
    model_config = ConfigDict(from_attributes=True)
    
class RentalBase(BaseModel):
    customer_name: str
    customer_surname: str
    rental_days: int
    return_datetime: datetime
    start_kilometers: int
    gas_tank_start: GasTankLevel
    car_id: int

class RentalCreate(RentalBase):
    pass

class RentalUpdate(BaseModel):
    end_kilometers: int
    gas_tank_end: GasTankLevel

class RentalOut(RentalBase):
    id: int
    company_id: int
    end_kilometers: Optional[int] = None
    gas_tank_end: Optional[GasTankLevel] = None
    model_config = ConfigDict(from_attributes=True)
    
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: str
    event_date: datetime

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int
    created_by_id: int
    model_config = ConfigDict(from_attributes=True)

class CalendarEvent(BaseModel):
    title: str
    start: datetime | date
    end: datetime | date
    type: str
    allDay: bool
    user_id: Optional[int] = None
    task_id: Optional[int] = None
    group_id: Optional[int] = None
    details: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: ProjectType
    store_location: Optional[str] = None
    store_address: Optional[str] = None
    company_id: int
    project_manager_id: Optional[int] = None
    start_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    estimated_budget: Optional[Decimal] = None
    notes: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    store_location: Optional[str] = None
    store_address: Optional[str] = None
    company_id: Optional[int] = None
    project_manager_id: Optional[int] = None
    start_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    estimated_budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    progress_percentage: Optional[int] = None
    notes: Optional[str] = None
    last_update: Optional[str] = None

class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus
    last_update: Optional[str] = None
    progress_percentage: Optional[int] = None

class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    actual_completion_date: Optional[date] = None
    actual_cost: Optional[Decimal] = None
    progress_percentage: int
    last_update: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Related objects
    company: CompanyOut  # Changed from CompanyBasicInfo to CompanyOut
    project_manager: Optional[UserBasicInfo] = None
    created_by: UserBasicInfo
    
    model_config = ConfigDict(from_attributes=True)

class ProjectListItem(BaseModel):
    """Simplified schema for project lists"""
    id: int
    name: str
    project_type: ProjectType
    status: ProjectStatus
    store_location: Optional[str] = None
    company_name: str
    project_manager_name: Optional[str] = None
    progress_percentage: int
    expected_completion_date: Optional[date] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Sale Schemas ---
class SaleBase(BaseModel):
    title: str
    description: Optional[str] = None
    sale_type: SaleType
    sale_amount: Decimal
    currency: str = "EUR"
    client_name: str
    client_company: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    salesperson_id: int
    company_id: Optional[int] = None
    project_id: Optional[int] = None
    lead_date: date
    proposal_date: Optional[date] = None
    expected_close_date: Optional[date] = None
    commission_rate: Decimal = Decimal('10.00')
    notes: Optional[str] = None
    source: Optional[str] = None

class SaleCreate(SaleBase):
    pass

class SaleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sale_type: Optional[SaleType] = None
    status: Optional[SaleStatus] = None
    sale_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    client_name: Optional[str] = None
    client_company: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    salesperson_id: Optional[int] = None
    company_id: Optional[int] = None
    project_id: Optional[int] = None
    proposal_date: Optional[date] = None
    close_date: Optional[date] = None
    expected_close_date: Optional[date] = None
    commission_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    source: Optional[str] = None

class SaleStatusUpdate(BaseModel):
    status: SaleStatus
    close_date: Optional[date] = None
    notes: Optional[str] = None

class SaleResponse(SaleBase):
    id: int
    status: SaleStatus
    close_date: Optional[date] = None
    commission_amount: Optional[Decimal] = None
    commission_status: CommissionStatus
    created_at: datetime
    updated_at: datetime
    
    # Related objects
    salesperson: UserBasicInfo
    company: Optional[CompanyOut] = None
    created_by: UserBasicInfo
    
    model_config = ConfigDict(from_attributes=True)

class SaleListItem(BaseModel):
    """Simplified schema for sale lists"""
    id: int
    title: str
    sale_type: SaleType
    status: SaleStatus
    sale_amount: Decimal
    currency: str
    client_name: str
    salesperson_name: str
    commission_amount: Optional[Decimal] = None
    lead_date: date
    close_date: Optional[date] = None
    expected_close_date: Optional[date] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Commission Rule Schemas ---
class CommissionRuleBase(BaseModel):
    employee_id: int
    sale_type: Optional[SaleType] = None
    base_commission_rate: Decimal = Decimal('10.00')
    min_sale_amount: Decimal = Decimal('0.00')
    tier1_threshold: Optional[Decimal] = None
    tier1_bonus_rate: Decimal = Decimal('0.00')
    tier2_threshold: Optional[Decimal] = None
    tier2_bonus_rate: Decimal = Decimal('0.00')
    tier3_threshold: Optional[Decimal] = None
    tier3_bonus_rate: Decimal = Decimal('0.00')
    effective_from: date
    effective_until: Optional[date] = None

class CommissionRuleCreate(CommissionRuleBase):
    pass

class CommissionRuleUpdate(BaseModel):
    sale_type: Optional[SaleType] = None
    base_commission_rate: Optional[Decimal] = None
    min_sale_amount: Optional[Decimal] = None
    tier1_threshold: Optional[Decimal] = None
    tier1_bonus_rate: Optional[Decimal] = None
    tier2_threshold: Optional[Decimal] = None
    tier2_bonus_rate: Optional[Decimal] = None
    tier3_threshold: Optional[Decimal] = None
    tier3_bonus_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None
    effective_until: Optional[date] = None

class CommissionRuleResponse(CommissionRuleBase):
    id: int
    is_active: bool
    created_at: datetime
    employee: UserBasicInfo
    created_by: UserBasicInfo
    
    model_config = ConfigDict(from_attributes=True)

# --- Monthly Commission Summary Schemas ---
class CommissionSummaryResponse(BaseModel):
    id: int
    employee_id: int
    year: int
    month: int
    total_sales_amount: Decimal
    closed_deals_count: int
    active_leads_count: int
    base_commission: Decimal
    tier_bonus: Decimal
    total_commission: Decimal
    payment_status: CommissionStatus
    payment_date: Optional[date] = None
    payment_notes: Optional[str] = None
    sales_breakdown: Optional[str] = None
    calculated_at: datetime
    last_updated: datetime
    
    # Related objects
    employee: UserBasicInfo
    calculated_by: UserBasicInfo
    
    model_config = ConfigDict(from_attributes=True)

class CommissionCalculationRequest(BaseModel):
    employee_id: int
    year: int
    month: int
    recalculate: bool = False  # Force recalculation if already exists

# --- Updated Payment Schemas ---
class PaymentBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: Decimal
    currency: str = "EUR"
    payment_type: PaymentType
    due_date: date
    employee_id: Optional[int] = None
    commission_summary_id: Optional[int] = None
    company_id: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_type: Optional[PaymentType] = None
    status: Optional[PaymentStatus] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    employee_id: Optional[int] = None
    commission_summary_id: Optional[int] = None
    company_id: Optional[int] = None
    category: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    paid_date: Optional[date] = None
    notes: Optional[str] = None

class PaymentApproval(BaseModel):
    approve: bool
    notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    paid_date: Optional[date] = None
    receipt_url: Optional[str] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related objects
    employee: Optional[UserBasicInfo] = None
    company: Optional[CompanyOut] = None
    commission_summary: Optional[CommissionSummaryResponse] = None
    created_by: UserBasicInfo
    approved_by: Optional[UserBasicInfo] = None
    
    # Computed properties
    is_income: bool
    is_expense: bool
    
    model_config = ConfigDict(from_attributes=True)

class PaymentListItem(BaseModel):
    """Simplified schema for payment lists"""
    id: int
    title: str
    amount: Decimal
    currency: str
    payment_type: PaymentType
    status: PaymentStatus
    due_date: date
    paid_date: Optional[date] = None
    employee_name: Optional[str] = None
    company_name: Optional[str] = None
    is_commission: bool
    is_income: bool
    is_expense: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Summary Schemas ---
class SalesDashboardSummary(BaseModel):
    # Current month
    current_month_sales: Decimal
    current_month_deals: int
    current_month_commission: Decimal
    
    # Previous month comparison
    previous_month_sales: Decimal
    previous_month_deals: int
    sales_growth_percentage: float
    
    # Pending items
    pending_leads: int
    pending_proposals: int
    pending_commission_payments: int
    overdue_payments: int
    
    # Top performers (this month)
    top_salesperson: str
    top_salesperson_amount: Decimal

class EmployeeCommissionSummary(BaseModel):
    employee_id: int
    employee_name: str
    current_month_sales: Decimal
    current_month_commission: Decimal
    ytd_sales: Decimal
    ytd_commission: Decimal
    pending_commission: Decimal
    last_payment_date: Optional[date] = None