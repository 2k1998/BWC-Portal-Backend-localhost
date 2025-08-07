# models.py - FIXED VERSION (Remove the incorrect import line)
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime, Table, Enum, Text, Numeric
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone
from database import Base
import enum

# --- EXISTING ENUMS (keep these) ---
class TaskStatus(str, enum.Enum):
    new = "new"
    received = "received"
    on_process = "on_process"
    pending = "pending"
    completed = "completed"
    loose_end = "loose_end"

class GasTankLevel(str, enum.Enum):
    empty = "Empty"
    quarter = "1/4"
    half = "1/2"
    three_quarters = "3/4"
    full = "Full"

class ProjectStatus(str, enum.Enum):
    planning = "planning"
    in_progress = "in_progress" 
    completed = "completed"
    on_hold = "on_hold"
    cancelled = "cancelled"

class ProjectType(str, enum.Enum):
    new_store = "new_store"
    renovation = "renovation"
    maintenance = "maintenance"
    expansion = "expansion"
    other = "other"

# --- NEW ENUMS (add these) ---
class SaleType(str, enum.Enum):
    store_opening = "store_opening"
    renovation = "renovation"
    maintenance_contract = "maintenance_contract"
    consulting = "consulting"
    car_rental = "car_rental"
    other = "other"

class SaleStatus(str, enum.Enum):
    lead = "lead"
    proposal_sent = "proposal_sent"
    negotiating = "negotiating"
    closed_won = "closed_won"
    closed_lost = "closed_lost"
    cancelled = "cancelled"

class CommissionStatus(str, enum.Enum):
    pending = "pending"
    calculated = "calculated"
    paid = "paid"
    disputed = "disputed"

class PaymentType(str, enum.Enum):
    commission_payment = "commission_payment"
    base_salary = "base_salary"
    bonus = "bonus"
    car_rental_income = "car_rental_income"
    business_expense = "business_expense"
    office_rent = "office_rent"
    utility_bill = "utility_bill"
    equipment_purchase = "equipment_purchase"
    other_income = "other_income"
    other_expense = "other_expense"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"
    disputed = "disputed"

# This is the association table for the many-to-many relationship between users and groups
group_members = Table(
    "group_members",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    birthday = Column(Date, nullable=True)
    role = Column(String, default="Agent", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    profile_picture_url = Column(String, nullable=True)

    @property
    def full_name(self) -> str:
        if self.first_name and self.surname:
            return f"{self.first_name} {self.surname}"
        return self.first_name or self.surname or self.email

    # Fixed relationships with explicit foreign_keys
    tasks = relationship("Task", foreign_keys="[Task.owner_id]", back_populates="owner")
    groups = relationship("Group", secondary=group_members, back_populates="members")
    events = relationship("Event", back_populates="creator")
    notifications = relationship("Notification", back_populates="user")
    contacts = relationship("Contact", back_populates="owner")
    daily_calls = relationship("DailyCall", back_populates="user")

# --- ADD THIS NEW MODEL ---
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # Foreign key to the user who owns this contact
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship back to the User model
    owner = relationship("User", back_populates="contacts")
# --- END NEW MODEL ---

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime)
    deadline = Column(DateTime)
    deadline_all_day = Column(Boolean, default=False)
    urgency = Column(Boolean, default=False)
    important = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.new)
    status_comments = Column(Text)
    status_updated_at = Column(DateTime)
    status_updated_by = Column(Integer, ForeignKey("users.id"))
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    # Fixed relationships with explicit foreign_keys
    owner = relationship("User", foreign_keys=[owner_id], back_populates="tasks")
    status_updater = relationship("User", foreign_keys=[status_updated_by])
    group = relationship("Group")
    company = relationship("Company")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")

    @validates('status')
    def validate_status(self, key, status):
        if status == TaskStatus.completed:
            self.completed = True
        else:
            self.completed = False
        return status

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    members = relationship("User", secondary=group_members, back_populates="groups")
    tasks = relationship("Task", back_populates="group")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    user = relationship("User")

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    vat_number = Column(String, unique=True, index=True, nullable=True)
    occupation = Column(String, nullable=True)
    creation_date = Column(Date, nullable=True)
    description = Column(String, nullable=True)
    tasks = relationship("Task", back_populates="company")
    cars = relationship("Car", back_populates="company", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    location = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="events")

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    license_plate = Column(String, unique=True, index=True, nullable=False)
    vin = Column(String, unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="cars")
    rentals = relationship("Rental", back_populates="car", cascade="all, delete-orphan")

class Rental(Base):
    __tablename__ = "rentals"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_surname = Column(String, nullable=False)
    rental_days = Column(Integer, nullable=False)
    return_datetime = Column(DateTime, nullable=False)
    start_kilometers = Column(Integer, nullable=False)
    gas_tank_start = Column(Enum(GasTankLevel), nullable=False)
    end_kilometers = Column(Integer, nullable=True)
    gas_tank_end = Column(Enum(GasTankLevel), nullable=True)
    is_locked = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    car = relationship("Car", back_populates="rentals")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="notifications")

# --- ADD THIS NEW MODEL ---
class DailyCall(Base):
    __tablename__ = "daily_calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)

    # How many times per day this contact should be called
    call_frequency_per_day = Column(Integer, default=1)
    
    # When is the next call due?
    next_call_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="daily_calls")
    contact = relationship("Contact")
# --- END NEW MODEL ---

# --- ADD THIS NEW MODEL ---
class TaskHistory(Base):
    __tablename__ = "task_histories"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_from = Column(Enum(TaskStatus), nullable=True)
    status_to = Column(Enum(TaskStatus), nullable=True)
    comment = Column(Text, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="history")
    changed_by = relationship("User")
# --- END NEW MODEL ---

# Add Project model
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_type = Column(Enum(ProjectType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.planning)
    
    # Location/Store info
    store_location = Column(String(255))
    store_address = Column(Text)
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company")
    
    # Project manager - Fixed with explicit foreign_keys
    project_manager_id = Column(Integer, ForeignKey("users.id"))
    project_manager = relationship("User", foreign_keys=[project_manager_id])
    
    # Dates
    start_date = Column(Date)
    expected_completion_date = Column(Date)
    actual_completion_date = Column(Date)
    
    # Budget
    estimated_budget = Column(Numeric(10, 2))
    actual_cost = Column(Numeric(10, 2))
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    
    # Notes and updates
    notes = Column(Text)
    last_update = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Fixed relationships with explicit foreign_keys
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f"<Project(name='{self.name}', status='{self.status}', company='{self.company.name if self.company else 'No Company'}')>"

# --- SALES & COMMISSION SYSTEM MODELS ---

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sale details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    sale_type = Column(Enum(SaleType), nullable=False)
    status = Column(Enum(SaleStatus), default=SaleStatus.lead)
    
    # Financial info
    sale_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    
    # Client info
    client_name = Column(String(255), nullable=False)
    client_company = Column(String(255))
    client_email = Column(String(255))
    client_phone = Column(String(50))
    
    # Relationships
    salesperson_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    salesperson = relationship("User", foreign_keys=[salesperson_id])
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company")
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project")
    
    # Important dates
    lead_date = Column(Date, nullable=False)
    proposal_date = Column(Date, nullable=True)
    close_date = Column(Date, nullable=True)
    expected_close_date = Column(Date, nullable=True)
    
    # Commission calculation
    commission_rate = Column(Numeric(5, 2), default=10.00)
    commission_amount = Column(Numeric(10, 2), nullable=True)
    commission_status = Column(Enum(CommissionStatus), default=CommissionStatus.pending)
    
    # Notes and tracking
    notes = Column(Text)
    source = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f"<Sale(title='{self.title}', amount={self.sale_amount}, status='{self.status}')>"
    
    def calculate_commission(self):
        """Calculate commission based on sale amount and rate"""
        if self.status == SaleStatus.closed_won and self.sale_amount:
            self.commission_amount = (self.sale_amount * self.commission_rate) / 100
            self.commission_status = CommissionStatus.calculated
        else:
            self.commission_amount = 0
        return self.commission_amount

class EmployeeCommissionRule(Base):
    __tablename__ = "employee_commission_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Employee
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee = relationship("User", foreign_keys=[employee_id])  # <-- Fixed with explicit foreign_keys
    
    # Commission rules
    sale_type = Column(Enum(SaleType), nullable=True)  # If null, applies to all sale types
    base_commission_rate = Column(Numeric(5, 2), default=10.00)  # Base percentage
    min_sale_amount = Column(Numeric(10, 2), default=0)  # Minimum sale amount for commission
    
    # Bonus tiers (optional)
    tier1_threshold = Column(Numeric(12, 2), nullable=True)  # Monthly sales target
    tier1_bonus_rate = Column(Numeric(5, 2), default=0)  # Additional % if tier1 reached
    tier2_threshold = Column(Numeric(12, 2), nullable=True)
    tier2_bonus_rate = Column(Numeric(5, 2), default=0)
    tier3_threshold = Column(Numeric(12, 2), nullable=True)
    tier3_bonus_rate = Column(Numeric(5, 2), default=0)
    
    # Settings
    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, default=datetime.utcnow)
    effective_until = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])  # <-- Fixed with explicit foreign_keys

class MonthlyCommissionSummary(Base):
    __tablename__ = "monthly_commission_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Period and employee
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee = relationship("User", foreign_keys=[employee_id])  # <-- Fixed with explicit foreign_keys
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    # Sales summary
    total_sales_amount = Column(Numeric(12, 2), default=0)
    closed_deals_count = Column(Integer, default=0)
    active_leads_count = Column(Integer, default=0)
    
    # Commission breakdown
    base_commission = Column(Numeric(10, 2), default=0)
    tier_bonus = Column(Numeric(10, 2), default=0)  # Bonus for reaching tiers
    total_commission = Column(Numeric(10, 2), default=0)
    
    # Payment status
    payment_status = Column(Enum(CommissionStatus), default=CommissionStatus.pending)
    payment_date = Column(Date, nullable=True)
    payment_notes = Column(Text)
    
    # Breakdown by sale type (JSON)
    sales_breakdown = Column(Text)  # JSON string with sale type breakdown
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calculated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    calculated_by = relationship("User", foreign_keys=[calculated_by_id])  # <-- Fixed with explicit foreign_keys

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    
    # Payment classification
    payment_type = Column(Enum(PaymentType), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    
    # Dates
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    
    # Employee relationship (for commission/salary payments)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee = relationship("User", foreign_keys=[employee_id])  # <-- Fixed with explicit foreign_keys
    
    # Commission summary relationship (for commission payments)
    commission_summary_id = Column(Integer, ForeignKey("monthly_commission_summaries.id"), nullable=True)
    commission_summary = relationship("MonthlyCommissionSummary")
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company")
    
    # Categories and tracking
    category = Column(String(100))
    receipt_url = Column(String(500))
    notes = Column(Text)
    
    # Approval workflow
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = relationship("User", foreign_keys=[approved_by_id])  # <-- Fixed with explicit foreign_keys
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])  # <-- Fixed with explicit foreign_keys
    
    def __repr__(self):
        return f"<Payment(title='{self.title}', amount={self.amount}, status='{self.status}')>"

    @property
    def is_income(self):
        """Returns True if this payment represents income"""
        income_types = [PaymentType.car_rental_income, PaymentType.other_income]
        return self.payment_type in income_types
    
    @property
    def is_expense(self):
        """Returns True if this payment represents an expense"""
        return not self.is_income