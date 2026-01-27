import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum

Base = declarative_base()

# Определение перечисления для SQLAlchemy
class ProductCategoryEnum(enum.Enum):
    ELECTRONICS = "ELECTRONICS"
    CLOTHING = "CLOTHING"
    FOOD = "FOOD"
    BOOKS = "BOOKS"
    OTHER = "OTHER"

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(SQLAlchemyEnum(ProductCategoryEnum), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=10)
    barcode = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Связи
    sales = relationship("Sale", back_populates="product")
    supplies = relationship("Supply", back_populates="product")

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String)
    discount = Column(Float, default=0.0)
    total_purchases = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    
    # Связи
    sales = relationship("Sale", back_populates="customer")

class Sale(Base):
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    
    # Связи
    product = relationship("Product", back_populates="sales", foreign_keys=[product_id])
    customer = relationship("Customer", back_populates="sales", foreign_keys=[customer_id])

class Supply(Base):
    __tablename__ = 'supplies'
    
    id = Column(Integer, primary_key=True)
    supplier = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    
    # Связи
    product = relationship("Product", back_populates="supplies", foreign_keys=[product_id])

class DatabaseManager:
    def __init__(self, db_path='store.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_product(self, name, category, price, quantity, min_stock=10, description=None, barcode=None):
        """Добавить товар"""
        with self.Session() as session:
            # Преобразуем строку в значение enum
            try:
                category_enum = ProductCategoryEnum[category]
            except KeyError:
                # Если строка не является именем enum, пробуем найти по значению
                for enum_member in ProductCategoryEnum:
                    if enum_member.value == category:
                        category_enum = enum_member
                        break
                else:
                    raise ValueError(f"Неизвестная категория: {category}")
            
            product = Product(
                name=name,
                category=category_enum,
                price=price,
                quantity=quantity,
                min_stock=min_stock,
                barcode=barcode,
                description=description
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
    
    def get_all_products(self):
        """Получить все товары"""
        with self.Session() as session:
            return session.query(Product).all()
    
    def get_product_by_id(self, product_id):
        """Получить товар по ID"""
        with self.Session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            return product
    
    def update_product(self, product_id, **kwargs):
        """Обновить товар"""
        with self.Session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                for key, value in kwargs.items():
                    if key == 'category':
                        # Преобразуем строку категории в enum
                        try:
                            value = ProductCategoryEnum[value]
                        except KeyError:
                            raise ValueError(f"Неизвестная категория: {value}")
                    
                    if hasattr(product, key):
                        setattr(product, key, value)
                session.commit()
                return True
        return False
    
    def delete_product(self, product_id):
        """Удалить товар"""
        with self.Session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
        return False
    
    def get_low_stock_products(self):
        """Получить товары с низким запасом"""
        with self.Session() as session:
            return session.query(Product).filter(Product.quantity < Product.min_stock).all()
    
    def add_customer(self, name, phone, email=None, discount=0.0):
        """Добавить клиента"""
        with self.Session() as session:
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                discount=discount
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer
    
    def get_all_customers(self):
        """Получить всех клиентов"""
        with self.Session() as session:
            return session.query(Customer).all()
    
    def get_customer_by_id(self, customer_id):
        """Получить клиента по ID"""
        with self.Session() as session:
            return session.query(Customer).filter(Customer.id == customer_id).first()
    
    def record_sale(self, product_id, quantity, customer_id=None):
        """Записать продажу"""
        with self.Session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product or product.quantity < quantity:
                return None
            
            customer = None
            if customer_id:
                customer = session.query(Customer).filter(Customer.id == customer_id).first()
            
            # Вычисляем сумму с учетом скидки
            total = product.price * quantity
            if customer and customer.discount > 0:
                total = total * (1 - customer.discount / 100)
            
            # Создаем продажу
            sale = Sale(
                product_id=product_id,
                customer_id=customer_id,
                quantity=quantity,
                price=product.price,
                total=total
            )
            
            # Обновляем количество товара
            product.quantity -= quantity
            
            # Обновляем статистику клиента
            if customer:
                customer.total_purchases += total
            
            session.add(sale)
            session.commit()
            session.refresh(sale)
            return sale
    
    def add_supply(self, supplier, product_id, quantity, cost):
        """Добавить поставку"""
        with self.Session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None
            
            supply = Supply(
                supplier=supplier,
                product_id=product_id,
                quantity=quantity,
                cost=cost
            )
            
            # Обновляем количество товара
            product.quantity += quantity
            
            session.add(supply)
            session.commit()
            session.refresh(supply)
            return supply
    
    def get_total_sales_amount(self):
        """Получить общую сумму продаж"""
        with self.Session() as session:
            total = session.query(func.sum(Sale.total)).scalar()
            return total or 0.0
    
    def get_recent_sales(self, days=7):
        """Получить последние продажи"""
        with self.Session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            return session.query(Sale).filter(Sale.date >= cutoff_date).order_by(Sale.date.desc()).all()
    
    def get_all_sales(self):
        """Получить все продажи"""
        with self.Session() as session:
            return session.query(Sale).order_by(Sale.date.desc()).all()
    
    def get_recent_supplies(self, days=30):
        """Получить последние поставки"""
        with self.Session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            return session.query(Supply).filter(Supply.date >= cutoff_date).order_by(Supply.date.desc()).all()
    
    def get_all_supplies(self):
        """Получить все поставки"""
        with self.Session() as session:
            return session.query(Supply).order_by(Supply.date.desc()).all()