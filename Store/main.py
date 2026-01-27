import sys
import os
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from ui.main_window import ModernMainWindow
from database.db_manager import DatabaseManager
from logic.store_logic import StoreLogic, ProductCategory
from reports.inventory_reports import InventoryReports

class StoreApp:
    """Главный класс приложения магазина"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Store Management System")
        
        # Инициализация компонентов
        self.db = DatabaseManager()
        self.logic = StoreLogic()
        self.reports = InventoryReports(self.db)
        
        # Создание главного окна
        self.main_window = ModernMainWindow()
        
        # Переменная для хранения выбранного товара
        self.selected_product_id = None
        
        # Подключение сигналов
        self.connect_signals()
        
        # Загрузка начальных данных
        self.load_initial_data()
        
    def connect_signals(self):
        """Подключение сигналов к слотам"""
        # Товары
        self.main_window.add_product_btn.clicked.connect(self.add_product)
        self.main_window.edit_product_btn.clicked.connect(self.edit_product)
        self.main_window.delete_product_btn.clicked.connect(self.delete_product)
        self.main_window.refresh_products_btn.clicked.connect(self.refresh_products)
        
        # Подключение сигнала выбора строки в таблице
        self.main_window.products_table.itemSelectionChanged.connect(self.on_product_selected)
        
        # Продажи
        self.main_window.process_sale_btn.clicked.connect(self.process_sale)
        self.main_window.refresh_sales_history_btn.clicked.connect(self.refresh_sales_history)
        
        # Поставки
        self.main_window.add_supply_btn.clicked.connect(self.add_supply)
        self.main_window.refresh_supplies_history_btn.clicked.connect(self.refresh_supplies_history)
        
        # Клиенты
        self.main_window.add_customer_btn.clicked.connect(self.add_customer)
        
        # Отчеты
        self.main_window.sales_report_btn.clicked.connect(self.show_sales_report)
        self.main_window.inventory_report_btn.clicked.connect(self.show_inventory_report)
        self.main_window.financial_report_btn.clicked.connect(self.show_financial_report)
        self.main_window.export_excel_btn.clicked.connect(self.export_to_excel)
        
    def load_initial_data(self):
        """Загрузка начальных данных"""
        # Загрузка товаров
        self.refresh_products()
        
        # Загрузка клиентов
        self.refresh_customers()
        
        # Обновление комбобоксов
        self.update_product_comboboxes()
        self.update_customer_combobox()
        
        # Загрузка истории
        self.refresh_sales_history()
        self.refresh_supplies_history()
        
        # Обновление статистики
        self.update_statistics()
    
    def update_product_comboboxes(self):
        """Обновление комбобоксов с товарами"""
        products = self.db.get_all_products()
        
        # Обновляем комбобокс на вкладке Продажи
        self.main_window.sale_product_combo.clear()
        for product in products:
            self.main_window.sale_product_combo.addItem(f"{product.name} (Остаток: {product.quantity})", product.id)
        
        # Обновляем комбобокс на вкладке Поставки
        self.main_window.supply_product_combo.clear()
        for product in products:
            self.main_window.supply_product_combo.addItem(f"{product.name} (Остаток: {product.quantity})", product.id)
    
    def update_customer_combobox(self):
        """Обновление комбобокса с клиентами"""
        customers = self.db.get_all_customers()
        
        # Обновляем комбобокс на вкладке Продажи
        self.main_window.sale_customer_combo.clear()
        self.main_window.sale_customer_combo.addItem("Без клиента", None)  # Опция без клиента
        for customer in customers:
            self.main_window.sale_customer_combo.addItem(f"{customer.name} ({customer.phone})", customer.id)
    
    def refresh_sales_history(self):
        """Обновление истории продаж"""
        try:
            sales = self.db.get_recent_sales(days=30)  # Получаем продажи за последние 30 дней
            
            table = self.main_window.sales_history_table
            table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                table.setItem(row, 0, QTableWidgetItem(str(sale.id)))
                table.setItem(row, 1, QTableWidgetItem(sale.date.strftime("%d.%m.%Y %H:%M")))
                
                # Получаем название товара
                product = self.db.get_product_by_id(sale.product_id)
                product_name = product.name if product else f"Товар ID:{sale.product_id}"
                table.setItem(row, 2, QTableWidgetItem(product_name))
                
                table.setItem(row, 3, QTableWidgetItem(str(sale.quantity)))
                table.setItem(row, 4, QTableWidgetItem(f"{sale.total:.2f} ₽"))
                
                # Получаем имя клиента
                if sale.customer_id:
                    customer = self.db.get_customer_by_id(sale.customer_id)
                    customer_name = customer.name if customer else f"Клиент ID:{sale.customer_id}"
                else:
                    customer_name = "Без клиента"
                table.setItem(row, 5, QTableWidgetItem(customer_name))
            
            table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Ошибка обновления истории продаж: {e}")
    
    def refresh_supplies_history(self):
        """Обновление истории поставок"""
        try:
            supplies = self.db.get_recent_supplies(days=30)  # Получаем поставки за последние 30 дней
            
            table = self.main_window.supplies_table
            table.setRowCount(len(supplies))
            
            for row, supply in enumerate(supplies):
                table.setItem(row, 0, QTableWidgetItem(str(supply.id)))
                table.setItem(row, 1, QTableWidgetItem(supply.date.strftime("%d.%m.%Y %H:%M")))
                table.setItem(row, 2, QTableWidgetItem(supply.supplier))
                
                # Получаем название товара
                product = self.db.get_product_by_id(supply.product_id)
                product_name = product.name if product else f"Товар ID:{supply.product_id}"
                table.setItem(row, 3, QTableWidgetItem(product_name))
                
                table.setItem(row, 4, QTableWidgetItem(str(supply.quantity)))
                table.setItem(row, 5, QTableWidgetItem(f"{supply.cost:.2f} ₽"))
            
            table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Ошибка обновления истории поставок: {e}")
    
    def on_product_selected(self):
        """Обработка выбора товара в таблице"""
        selected_items = self.main_window.products_table.selectedItems()
        
        if selected_items:
            # Получаем ID товара из первого столбца выбранной строки
            row = selected_items[0].row()
            product_id = int(self.main_window.products_table.item(row, 0).text())
            
            self.selected_product_id = product_id
            self.main_window.edit_product_btn.setEnabled(True)
            self.main_window.delete_product_btn.setEnabled(True)
            
            # Заполняем форму данными выбранного товара
            self.load_product_to_form(product_id)
        else:
            self.selected_product_id = None
            self.main_window.edit_product_btn.setEnabled(False)
            self.main_window.delete_product_btn.setEnabled(False)
    
    def load_product_to_form(self, product_id):
        """Загрузка данных товара в форму"""
        product = self.db.get_product_by_id(product_id)
        if product:
            self.main_window.product_name_input.setText(product.name)
            
            # Устанавливаем категорию
            if hasattr(product.category, 'value'):
                category_text = product.category.value
            elif isinstance(product.category, str):
                try:
                    category_enum = ProductCategory[product.category]
                    category_text = category_enum.value
                except KeyError:
                    category_text = product.category
            else:
                category_text = str(product.category)
            
            index = self.main_window.product_category_input.findText(category_text)
            if index >= 0:
                self.main_window.product_category_input.setCurrentIndex(index)
            
            self.main_window.product_price_input.setValue(product.price)
            self.main_window.product_quantity_input.setValue(product.quantity)
            self.main_window.product_min_stock_input.setValue(product.min_stock)
    
    def add_product(self):
        """Добавление товара"""
        try:
            name = self.main_window.product_name_input.text().strip()

            selected_category_text = self.main_window.product_category_input.currentText()

            # Находим соответствующее значение перечисления
            category_enum = None
            for cat in ProductCategory:
                if cat.value == selected_category_text:
                    category_enum = cat
                    break
        
            if category_enum is None:
                self.main_window.show_message("Ошибка", f"Неизвестная категория: {selected_category_text}")
                return

            category = category_enum.name  # Используем .name вместо .value

            price = self.main_window.product_price_input.value()
            quantity = self.main_window.product_quantity_input.value()
            min_stock = self.main_window.product_min_stock_input.value()
            
            if not name:
                self.main_window.show_message("Ошибка", "Введите название товара")
                return
            
            # Используем логику
            product = self.logic.add_product(name, category, price, quantity, min_stock)
            
            # Сохраняем в БД - передаем имя enum
            self.db.add_product(
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                min_stock=min_stock
            )
            
            self.main_window.show_message("Успех", f"Товар '{name}' добавлен!")
            self.refresh_products()
            self.clear_product_form()
            
        except Exception as e:
            self.main_window.show_message("Ошибка", str(e))
    
    def edit_product(self):
        """Редактирование товара"""
        if self.selected_product_id is None:
            self.main_window.show_message("Ошибка", "Выберите товар для редактирования")
            return
        
        try:
            name = self.main_window.product_name_input.text().strip()
            selected_category_text = self.main_window.product_category_input.currentText()
            
            # Находим соответствующее значение перечисления
            category_enum = None
            for cat in ProductCategory:
                if cat.value == selected_category_text:
                    category_enum = cat
                    break
            
            if category_enum is None:
                self.main_window.show_message("Ошибка", f"Неизвестная категория: {selected_category_text}")
                return
            
            category = category_enum.name
            price = self.main_window.product_price_input.value()
            quantity = self.main_window.product_quantity_input.value()
            min_stock = self.main_window.product_min_stock_input.value()
            
            if not name:
                self.main_window.show_message("Ошибка", "Введите название товара")
                return
            
            # Обновляем товар в БД
            success = self.db.update_product(
                product_id=self.selected_product_id,
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                min_stock=min_stock
            )
            
            if success:
                self.main_window.show_message("Успех", f"Товар '{name}' обновлен!")
                self.refresh_products()
                self.clear_product_form()
                self.main_window.edit_product_btn.setEnabled(False)
                self.main_window.delete_product_btn.setEnabled(False)
                self.selected_product_id = None
            else:
                self.main_window.show_message("Ошибка", "Не удалось обновить товар")
                
        except Exception as e:
            self.main_window.show_message("Ошибка", str(e))
    
    def delete_product(self):
        """Удаление товара"""
        if self.selected_product_id is None:
            self.main_window.show_message("Ошибка", "Выберите товар для удаления")
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self.main_window,
            'Подтверждение удаления',
            f'Вы уверены, что хотите удалить этот товар?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем товар из БД
                success = self.db.delete_product(self.selected_product_id)
                
                if success:
                    self.main_window.show_message("Успех", "Товар удален!")
                    self.refresh_products()
                    self.clear_product_form()
                    self.main_window.edit_product_btn.setEnabled(False)
                    self.main_window.delete_product_btn.setEnabled(False)
                    self.selected_product_id = None
                else:
                    self.main_window.show_message("Ошибка", "Не удалось удалить товар")
                    
            except Exception as e:
                self.main_window.show_message("Ошибка", str(e))
    
    def refresh_products(self):
        """Обновление списка товаров"""
        products = self.db.get_all_products()
        
        table = self.main_window.products_table
        table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            table.setItem(row, 1, QTableWidgetItem(product.name))

            # Получаем читаемое название категории
            if hasattr(product.category, 'value'):
                category_display = product.category.value
            elif isinstance(product.category, str):
                try:
                    category_enum = ProductCategory[product.category]
                    category_display = category_enum.value
                except KeyError:
                    category_display = product.category
            else:
                category_display = str(product.category)
            
            table.setItem(row, 2, QTableWidgetItem(category_display))
            
            table.setItem(row, 3, QTableWidgetItem(f"{product.price:.2f} ₽"))
            table.setItem(row, 4, QTableWidgetItem(str(product.quantity)))
            table.setItem(row, 5, QTableWidgetItem(str(product.min_stock)))
            
            # Статус
            status = "✅ В наличии"
            if product.quantity == 0:
                status = "❌ Нет в наличии"
            elif product.quantity < product.min_stock:
                status = "⚠️ Низкий запас"
            
            table.setItem(row, 6, QTableWidgetItem(status))
        
        table.resizeColumnsToContents()
        
        # Обновляем комбобоксы с товарами
        self.update_product_comboboxes()
    
    def clear_product_form(self):
        """Очистка формы товара"""
        self.main_window.product_name_input.clear()
        self.main_window.product_price_input.setValue(0)
        self.main_window.product_quantity_input.setValue(0)
        self.main_window.product_min_stock_input.setValue(10)
    
    def process_sale(self):
        """Обработка продажи"""
        try:
            # Получаем выбранный товар из комбобокса
            product_index = self.main_window.sale_product_combo.currentIndex()
            if product_index == -1:
                self.main_window.show_message("Ошибка", "Выберите товар")
                return
            
            product_id = self.main_window.sale_product_combo.itemData(product_index)
            quantity = self.main_window.sale_quantity_spin.value()
            
            # Получаем выбранного клиента
            customer_index = self.main_window.sale_customer_combo.currentIndex()
            customer_id = self.main_window.sale_customer_combo.itemData(customer_index)
            
            if quantity <= 0:
                self.main_window.show_message("Ошибка", "Введите количество больше 0")
                return
            
            sale = self.db.record_sale(product_id, quantity, customer_id)
            
            if sale:
                self.main_window.show_message("Успех", f"Продажа оформлена на сумму {sale.total:.2f} ₽")
                self.refresh_products()
                self.refresh_sales_history()
                self.clear_sale_form()
                self.update_statistics()
            else:
                self.main_window.show_message("Ошибка", "Не удалось оформить продажу")
                
        except Exception as e:
            self.main_window.show_message("Ошибка", str(e))
    
    def clear_sale_form(self):
        """Очистка формы продажи"""
        self.main_window.sale_quantity_spin.setValue(1)
    
    def add_supply(self):
        """Добавление поставки"""
        try:
            supplier = self.main_window.supplier_input.text().strip()
            quantity = self.main_window.supply_quantity_spin.value()
            cost = self.main_window.supply_cost_input.value()
            
            if not supplier:
                self.main_window.show_message("Ошибка", "Введите поставщика")
                return
            
            # Получаем выбранный товар из комбобокса
            product_index = self.main_window.supply_product_combo.currentIndex()
            if product_index == -1:
                self.main_window.show_message("Ошибка", "Выберите товар")
                return
            
            product_id = self.main_window.supply_product_combo.itemData(product_index)
            
            if quantity <= 0:
                self.main_window.show_message("Ошибка", "Введите количество больше 0")
                return
            
            if cost <= 0:
                self.main_window.show_message("Ошибка", "Введите стоимость поставки больше 0")
                return
            
            supply = self.db.add_supply(supplier, product_id, quantity, cost)
            
            if supply:
                self.main_window.show_message("Успех", f"Поставка добавлена!")
                self.refresh_products()
                self.refresh_supplies_history()
                self.clear_supply_form()
                self.update_statistics()
                
        except Exception as e:
            self.main_window.show_message("Ошибка", str(e))
    
    def clear_supply_form(self):
        """Очистка формы поставки"""
        self.main_window.supplier_input.clear()
        self.main_window.supply_quantity_spin.setValue(1)
        self.main_window.supply_cost_input.setValue(0)
    
    def add_customer(self):
        """Добавление клиента"""
        try:
            name = self.main_window.customer_name_input.text().strip()
            phone = self.main_window.customer_phone_input.text().strip()
            email = self.main_window.customer_email_input.text().strip()
            discount = self.main_window.customer_discount_spin.value()
            
            if not name or not phone:
                self.main_window.show_message("Ошибка", "Заполните обязательные поля")
                return
            
            customer = self.db.add_customer(name, phone, email, discount)
            
            if customer:
                self.main_window.show_message("Успех", f"Клиент '{name}' добавлен!")
                self.refresh_customers()
                self.clear_customer_form()
                
        except Exception as e:
            self.main_window.show_message("Ошибка", str(e))
    
    def refresh_customers(self):
        """Обновление списка клиентов"""
        customers = self.db.get_all_customers()
        
        table = self.main_window.customers_table
        table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            table.setItem(row, 1, QTableWidgetItem(customer.name))
            table.setItem(row, 2, QTableWidgetItem(customer.phone))
            table.setItem(row, 3, QTableWidgetItem(customer.email))
            table.setItem(row, 4, QTableWidgetItem(f"{customer.discount}%"))
        
        table.resizeColumnsToContents()
        
        # Обновляем комбобокс с клиентами
        self.update_customer_combobox()
    
    def clear_customer_form(self):
        """Очистка формы клиента"""
        self.main_window.customer_name_input.clear()
        self.main_window.customer_phone_input.clear()
        self.main_window.customer_email_input.clear()
        self.main_window.customer_discount_spin.setValue(0)
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            # Общие продажи
            total_sales = self.db.get_total_sales_amount()
            self.main_window.total_sales_label.setText(f"Общие продажи: {total_sales:.2f} ₽")
            
            # Товары на складе
            products = self.db.get_all_products()
            total_products = sum(p.quantity for p in products)
            self.main_window.total_products_label.setText(f"Товаров на складе: {total_products}")
            
            # Товары с низким запасом
            low_stock = len(self.db.get_low_stock_products())
            self.main_window.low_stock_label.setText(f"Товаров с низким запасом: {low_stock}")
            
        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
    
    def show_sales_report(self):
        """Показать отчет по продажам"""
        report = self.reports.generate_sales_report()
        self.main_window.report_text.setPlainText(report)
    
    def show_inventory_report(self):
        """Показать отчет по инвентарю"""
        report = self.reports.generate_inventory_report()
        self.main_window.report_text.setPlainText(report)
    
    def show_financial_report(self):
        """Показать финансовый отчет"""
        report = self.reports.generate_financial_report()
        self.main_window.report_text.setPlainText(report)
    
    def export_to_excel(self):
        """Экспорт в Excel"""
        try:
            filename = self.reports.export_to_excel()
            self.main_window.show_message("Успех", f"Данные экспортированы в {filename}")
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def run(self):
        """Запуск приложения"""
        self.main_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    # Создаем необходимые директории
    os.makedirs('exports', exist_ok=True)
    
    # Запускаем приложение
    store_app = StoreApp()
    store_app.run()