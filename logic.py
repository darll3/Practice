import sys
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QMessageBox, QLineEdit
from interface import Program
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from datetime import datetime
from dateutil.relativedelta import relativedelta


class interface_user(Program):
    def __init__(self):
        super().__init__()

        # После твоего цикла добавь эту строку:
        self.comm_val_input.setValidator(self.numeric_validator)
        #выпадающий список для мес/лет
        self.term_unit_combo.currentIndexChanged.connect(self.update_term_validation)
        # выпадающий список для комиссий руб/проценты
        self.comm_unit_combo.currentTextChanged.connect(self.update_comm_validator)

        #список всех полей ввода для проверки, чтобы в начале не ставилась точка
        money_fields = [
            self.sum_input,
            self.rate_input_fixed,
            self.rate_input,
            self.early_sum_input,
            self.comm_val_input
        ]
        # для кадого поля в списке делаем проверку
        for field in money_fields:
            # validate_input_start удалит точку или запятую если ввели первой
            field.textChanged.connect(lambda _, f=field: self.validate_input_start(f))
        # вызываем функции сразу, чтобы лимиты работали сразу
        self.update_term_validation()
        self.update_comm_validator()
        # кнопку расчитать связываем с функцией расчета
        self.btn_calculate.clicked.connect(self.start_calculation)
        # при запуске теперь всегда будет сегодняшняя дата
        self.date_input.setText(datetime.now().strftime("%d.%m.%Y"))

        #если начинается ввод в поле то убираем красную подстветку
        self.sum_input.textChanged.connect(lambda: self.clear_single_error(self.sum_input))
        self.term_input.textChanged.connect(lambda: self.clear_single_error(self.term_input))
        self.custom_day_input.textChanged.connect(lambda: self.clear_single_error(self.custom_day_input))
        # если нажаи на кнопки выбора дня тоже убираем ошибку
        self.btn_issue_day.clicked.connect(lambda: self.clear_single_error(self.custom_day_input))
        self.btn_last_day.clicked.connect(lambda: self.clear_single_error(self.custom_day_input))
        # убравление чекбоксами, вкл или выкл ввод параметров
        self.check_early.stateChanged.connect(self.handle_early_check)
        self.check_comm.stateChanged.connect(self.handle_comm_check)

    def update_comm_validator(self):
        # проверяем какие единицы измерения выбраны
        if self.comm_unit_combo.currentText() == "%":
           #  если проуенты то устанавливанием ограничения от 0 доо 100 и два знака после запятой
           self.comm_val_input.setValidator(QDoubleValidator(1.0, 100.0, 2))
        else:
            #если сумма то от но до миллиарда и тож двумя знаками после запятой
            self.comm_val_input.setValidator(QDoubleValidator(0.0, 999999999.0, 2))

    def update_term_validation(self):
        #для срока кредита ограничения
        self.term_input.setValidator(QIntValidator(1, 999))

    #сброс подсветки
    def clear_single_error(self, widget):
        # меняем ошибку на нет, потом забываем что поле было красное и применем стандартный вид полю
        widget.setProperty("error", "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def clean_numeric_input(self, widget):
        # берем текст из поля и убираем пробелы
        raw_text = widget.text().strip().replace(' ', '')
        #заменяем запятую на точку
        clean_text = raw_text.replace(',', '.')
        # если точек больше одной то, склевиваем все до последней точки, которая отделяет две цифры
        if clean_text.count('.') > 1:
            parts = clean_text.split('.')
            return "".join(parts[:-1]) + "." + parts[-1]
        return clean_text

    def start_calculation(self):
        # создаем пустые списки для хранения полей и текстов ошибок
        errors_widgets = []
        error_messages = []
        # для объекта дата, изначально пустая
        issue_date_obj = None

        # применяем вот ту очистку поле ввода суммы
        # убираем лишние точки запятые пробелы
        sum_text = self.clean_numeric_input(self.sum_input)
        # для досрочного погашения если галочка стоит
        early_sum_text = ""
        if self.check_early.isChecked():
            early_sum_text = self.clean_numeric_input(self.early_sum_input)

        # проверка суммы, если меньше нуля ошибка
        try:
            if not sum_text or float(sum_text) <= 0:
                errors_widgets.append(self.sum_input)
                error_messages.append("• Сумма кредита (число больше 0)")
        except ValueError:
            # если есть нечисловые символы, то ошибка
            errors_widgets.append(self.sum_input)
            error_messages.append("• Введите корректную сумму")

        # Дата выдачи
        # берем текст без лишник символов
        date_text = self.date_input.text().strip()
        # узнаем сегодняшнее число
        today = datetime.now()
        try:
            # превращаем текст в формат даты, если не в виде ДД.ММ.ГГГГ то будет ошибка
            issue_date_obj = datetime.strptime(date_text, "%d.%m.%Y")
            # кредит не может быть выдан завтра
            if issue_date_obj > today:
                errors_widgets.append(self.date_input)
                error_messages.append("• Дата выдачи не может быть в будущем")
        except ValueError:
            errors_widgets.append(self.date_input)
            error_messages.append("• Введите корректную дату выдачи (ДД.ММ.ГГГГ)")

        # Срок кредита
        term_text = self.term_input.text().strip()
        if not term_text:
            errors_widgets.append(self.term_input)
            error_messages.append("• Введите срок кредита")
        else:
            try:
                # срок всегд ацелое число
                term_val = int(term_text)
                # проверяем  что выбрано лет или мес
                unit = self.term_unit_combo.currentText()
                # если лет то не больше 50
                if unit == "лет":
                    if not (1 <= term_val <= 50):
                        errors_widgets.append(self.term_input)
                        error_messages.append("• Срок кредита должен быть от 1 до 50 лет")
                else:
                    # если месяц то не больше 600
                    if not (1 <= term_val <= 600):
                        errors_widgets.append(self.term_input)
                        error_messages.append("• Срок должен быть от 1 до 600 месяцев")
            except ValueError:
                errors_widgets.append(self.term_input)
                error_messages.append("• Введите число в поле срока")

        # Ставка
        if self.btn_fixed.isChecked():
            # Получаем очищенный текст из поля фиксированной ставки
            rate_text = self.clean_numeric_input(self.rate_input_fixed)
            if not rate_text:
                errors_widgets.append(self.rate_input_fixed)
                error_messages.append("• Введите процентную ставку")
            else:
                try:
                    val = float(rate_text)
                    if not (1 <= val <= 100):
                        errors_widgets.append(self.rate_input_fixed)
                        error_messages.append("• Ставка должна быть от 1% до 100%")
                except ValueError:
                    errors_widgets.append(self.rate_input_fixed)
                    error_messages.append("• Введите корректное число в поле ставки")
        elif self.btn_variable.isChecked():
            # Берем текст, очищаем его от пробелов и меняем запятую на точку
            raw_rate = self.clean_numeric_input(self.rate_input)

            if not raw_rate:
                errors_widgets.append(self.rate_input)
                error_messages.append("• Введите начальную процентную ставку")
            else:
                try:
                    rate_val = float(raw_rate)
                    if not (1 <= rate_val <= 100):
                        errors_widgets.append(self.rate_input)
                        error_messages.append("• Ставка должна быть от 1% до 100%")
                except ValueError:
                    errors_widgets.append(self.rate_input)
                    error_messages.append("• Некорректный формат ставки")

        # Вид платежа
        # проверяем нажат ли кнопка типа платежа
        if not self.btn_annity.isChecked() and not self.btn_diff.isChecked():
            error_messages.append("• Вид платежа")
        # проверяем тип выплат
        if not self.btn_interest_only.isChecked() and not self.btn_full_pay.isChecked():
            error_messages.append("• Тип первого платежа")

        # День платежа
        if self.btn_issue_day.isChecked() or self.btn_last_day.isChecked():
            # Сесли выраны кнопки , то убираем ошибку с поля ввода
            self.clear_single_error(self.custom_day_input)
        else:
            day_text = self.custom_day_input.text().strip()
            if not day_text:
                errors_widgets.append(self.custom_day_input)
                error_messages.append("• Введите день ежемесячного платежа")
            else:
                try:
                    day_val = int(day_text)
                    # в месяце не бывает больше 31 дня, добавляем сообщение об ошибке
                    if not (1 <= day_val <= 31):
                        errors_widgets.append(self.custom_day_input)
                        error_messages.append("• День платежа должен быть от 1 до 31")
                except ValueError:
                    errors_widgets.append(self.custom_day_input)
                    error_messages.append("• Введите число в поле дня платежа")

        # Дострочка
        if self.check_early.isChecked():
            early_sum_txt = early_sum_text
            if not early_sum_txt or float(early_sum_txt or 0) <= 0:
                errors_widgets.append(self.early_sum_input)
                error_messages.append("• Сумма досрочного платежа")

            early_date_text = self.early_date_input.text().strip()
            try:
                early_date_obj = datetime.strptime(early_date_text, "%d.%m.%Y")
                # нельзя погасить кредит до того как ты его получил
                if issue_date_obj and early_date_obj < issue_date_obj:
                    errors_widgets.append(self.early_date_input)
                    error_messages.append("• Досрочка не может быть раньше выдачи")
            except ValueError:
                errors_widgets.append(self.early_date_input)
                error_messages.append("• Дата досрочного платежа")
            # проверка нажатия кнопок по поводоу типа досрочного погашения
            if not self.btn_reduce_sum.isChecked() and not self.btn_reduce_term.isChecked():
                error_messages.append("• Тип досрочного погашения")
            # проверяем кнопку о переодичности погашения
            if not self.btn_once.isChecked() and not self.btn_monthly.isChecked() and not self.btn_yearly.isChecked():
                error_messages.append("• Периодичность досрочного платежа")

        # Комиссии
        if self.check_comm.isChecked():
            comm_val_txt = self.clean_numeric_input(self.comm_val_input)

            # Проверяем, выбрана ли кнопка типа комиссии в QButtonGroup
            if self.comm_group.checkedButton() is None:
                # Добавляем обе кнопки в список ошибок для визуальной подсветки
                errors_widgets.append(self.btn_comm_once)
                errors_widgets.append(self.btn_comm_month)
                error_messages.append("• Выберите тип комиссии (Единовременная или Ежемесячная)")

            if not comm_val_txt:
                errors_widgets.append(self.comm_val_input)
                error_messages.append("• Введите значение комиссии")
            else:
                try:
                    comm_float = float(comm_val_txt)

                    # Проверяем диапазон, если выбраны проценты
                    if self.comm_unit_combo.currentText() == "%":
                        if not (1 <= comm_float <= 100):
                            errors_widgets.append(self.comm_val_input)
                            error_messages.append("• Комиссия в % должна быть от 1 до 100")

                    # Если выбраны рубли, просто проверяем что сумма больше 0
                    elif comm_float <= 0:
                        errors_widgets.append(self.comm_val_input)
                        error_messages.append("• Сумма комиссии должна быть больше 0")

                except ValueError:
                    errors_widgets.append(self.comm_val_input)
                    error_messages.append("• Введите корректное число в поле комиссии")

        # Вывод ошибок
        if error_messages:
            # если список не пуст подсвечиваем поля красным
            self.highlight_errors(errors_widgets)
            # создаем вспылвающее поле
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Ошибка заполнения")
            msg.setText("Для расчета необходимо:")
            # делаем переносы строки в тексте ошибок
            msg.setInformativeText("\n".join(error_messages))
            # показываеи окно ошибки
            msg.exec()
            # выходим из функции, чтобы расчет не начался
            return
        # если ошибок нет, снимаем всю краснуб подстветку
        self.clear_all_errors()

        # Рассчет
        try:
            # превращаем очищенную строку в дробное число
            sum_credit = float(sum_text)
            term_val = int(self.term_input.text())
            # приводим срок к меясцам
            months = term_val * 12 if self.term_unit_combo.currentText() == "лет" else term_val

            # День платежа
            if self.btn_issue_day.isChecked():
                # день при выдаче
                payment_day = issue_date_obj.day
            elif self.btn_last_day.isChecked():
                payment_day = 31
            else:
                payment_day = int(self.custom_day_input.text() or 1)

            # данные по ставкам
            rates_history = []
            if self.btn_fixed.isChecked():
                # одна ставка на весь период
                rate_val = self.clean_numeric_input(self.rate_input_fixed)
                rates_history.append((self.date_input.text(), float(rate_val or 0)))
            else:
                # ставка изменяемая
                rate_val = self.clean_numeric_input(self.rate_input)
                rates_history.append((self.date_input.text(), float(rate_val or 0)))
                for i in range(self.rate_changes_layout.count()):
                    item = self.rate_changes_layout.itemAt(i)
                    if item and item.widget():
                        line_edits = item.widget().findChildren(QLineEdit)
                        # добавляем в историю дата процент
                        if len(line_edits) >= 2 and line_edits[0].text() and line_edits[1].text():
                            clean_rate = self.clean_numeric_input(line_edits[1])
                            rates_history.append((line_edits[0].text(), float(clean_rate)))

            # создаем словарь с параметрами досрочки
            early_params = None
            if self.check_early.isChecked() and self.early_sum_input.text():
                early_params = {
                    'sum': float(early_sum_text),
                    'date': datetime.strptime(self.early_date_input.text(), "%d.%m.%Y"),
                    'type': 'reduce_sum' if self.btn_reduce_sum.isChecked() else 'reduce_term'
                }

            # создаем словарь с параметрами комиссии
            comm_params = None
            if self.check_comm.isChecked() and self.comm_val_input.text():
                comm_params = {
                    'val': float(self.clean_numeric_input(self.comm_val_input)),
                    'unit': self.comm_unit_combo.currentText(),
                    'once': self.btn_comm_once.isChecked()
                }

            # Вызов расчета
            schedule = self.build_payment_schedule(
                sum_credit, rates_history, months,
                'annuity' if self.btn_annity.isChecked() else 'diff',
                payment_day, self.btn_interest_only.isChecked(), early_params, comm_params
            )

            # отображение результатов
            if schedule:
                # считаем сумму всех выплат пользователя
                total_paid = sum(row[1] for row in schedule)

                # Переплата
                total_overpay = max(0.0, total_paid - sum_credit)

                # записываем итоги в правильные поля
                self.res_payment.setText(f"{schedule[0][1]:.2f} руб.")
                self.res_total.setText(f"{total_paid:.2f} руб.")
                self.res_overpay.setText(f"{total_overpay:.2f} руб.")

                # заполеяем таблицу на экране
                self.update_table(schedule)

        except Exception as e:
            # если где то чтото не вышло, то выводим сообщение об ошибке расчета
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")

    def build_payment_schedule(self, sum_credit, rates_history, months, payment_type, payment_day, first_only_interest,
                               early_params, comm_params):
        # список в который складываются строки таблицы
        schedule = []
        # остаток долга равен всей сумме кредита
        remaining_debt = sum_credit
        # текст из поля даты превращаем в объект от которого будем отсчитывать месяцы
        start_date = datetime.strptime(self.date_input.text(), "%d.%m.%Y")
        # берем самую первую ставку из истории
        current_rate = rates_history[0][1]

        #рассчет  аннуитетного платежа для сохранения размера при уменьшении срока
        base_m_rate = current_rate / (12 * 100)
        if first_only_interest and months > 1:
            # Если первый месяц — только проценты, то тело кредита распределяется на (months - 1)
            base_annuity_payment = sum_credit * (base_m_rate / (1 - (1 + base_m_rate) ** -(months - 1)))
        else:
            base_annuity_payment = sum_credit * (base_m_rate / (1 - (1 + base_m_rate) ** -months))

        # счетчик месяцев
        m = 1
        # пока не закончились месяцы и остаток долга больше 1 копейки
        while m <= months and remaining_debt > 0.01:
            # считаем дату платежа
            pay_date = start_date + relativedelta(months=m, day=payment_day)

            # Проверка изменения ставки, идем по списку дат когда она должна измениться
            for d_str, r_val in rates_history:
                # если дата платежа наступила или прошла дату изменения то обновляем ставку
                if pay_date >= datetime.strptime(d_str, "%d.%m.%Y"):
                    current_rate = r_val

            # месячная процентная ставка в долях
            m_rate = current_rate / (12 * 100)
            # проценты за текущий месяц (всегда считаются от остатка долга)
            interest = remaining_debt * m_rate

            # Расчет планового платежа (тело и общая сумма) до учета досрочки
            if m == 1 and first_only_interest:
                # если первый платеж только проценты - не уменьшаем долг
                plan_principal = 0.0
                # платим только проценты
                plan_payment = interest
            else:
                m_left = months - m + 1
                # Платеж и основной долг
                if payment_type == 'annuity':
                    # Проверяем выбранную стратегию досрочки
                    if early_params and early_params['type'] == 'reduce_term':
                        # Если уменьшаем срок -> платеж держим базовым (не пересчитываем на уменьшение)
                        plan_payment = base_annuity_payment
                    else:
                        # Если снижаем платеж -> пересчитываем аннуитет по стандартной формуле от текущего остатка
                        plan_payment = remaining_debt * (m_rate / (1 - (1 + m_rate) ** -m_left))

                    plan_principal = plan_payment - interest
                else:
                    # если дифф, то
                    plan_principal = remaining_debt / m_left
                    # полный платеж
                    plan_payment = plan_principal + interest

            # Корректировка на случай, если начисленный плановый долг превысил фактический остаток
            if plan_principal > remaining_debt:
                plan_principal = remaining_debt
                plan_payment = plan_principal + interest

            # Если досрочка, то ищем её по совпадению месяца и года (чтобы привязать к плановой дате)
            total_early_this_month = 0.0
            if early_params:
                # дата когда начинается досрочка
                e_date = early_params['date']
                is_pay_month = False

                # если разовая досрочка то проверяем совпадение месяца и года
                if self.btn_once.isChecked() and pay_date.month == e_date.month and pay_date.year == e_date.year:
                    is_pay_month = True
                # если ежемесячная платим каждый раз, когда дата платежа больше или равна дате начала досрочки
                elif self.btn_monthly.isChecked() and pay_date >= e_date:
                    is_pay_month = True
                # если ежегодная то платим раз в год в тот же месяц
                elif self.btn_yearly.isChecked() and pay_date >= e_date and pay_date.month == e_date.month:
                    is_pay_month = True

                if is_pay_month:
                    # Досрочка гасит максимум то, что осталось от долга после планового платежа
                    available_debt = remaining_debt - plan_principal
                    # берем сумму досрочки но не больше суммы задолженности
                    total_early_this_month = min(early_params['sum'], max(0.0, available_debt))

            # Собираем итоговые значения для одной строки таблицы
            # В колону основной долг идет плановое погашение и досрочка
            total_principal_paid = plan_principal + total_early_this_month
            # В колону "Платеж" идет фактический платеж пользователя (план + досрочка)
            total_user_payment = plan_payment + total_early_this_month

            # Динамический расчет комиссий (руб или %) и типов (разовая/ежемесячная)
            current_comm = 0.0
            if comm_params:
                # Считаем значение комиссии в рублях
                if comm_params['unit'] == '%':
                    comm_value = sum_credit * (comm_params['val'] / 100)
                else:
                    comm_value = comm_params['val']

                # Распределяем по типу
                if comm_params['once'] and m == 1:
                    current_comm = comm_value  # Единовременная,падает только в первый месяц
                elif not comm_params['once']:
                    current_comm = comm_value  # Ежемесячная,падает в каждый месяц графика

            # Добавляем комиссию к платежу пользователя (не уменьшает долг)
            total_user_payment += current_comm

            # уменьшаем общую задолженность на выплаченный плановый кредит и досрочку
            remaining_debt -= total_principal_paid

            # Чтобы остаток не стал -0.00
            if remaining_debt < 0.01:
                remaining_debt = 0.0

            # собираем данные для одной строки таблицы
            schedule.append((
                pay_date.strftime("%d.%m.%Y"),
                round(total_user_payment, 2),  # Итоговый платеж (включая комиссию и досрочку)
                round(total_principal_paid, 2),  # Всего пошло в тело долга (план + досрочка)
                round(interest, 2),  # Начисленные проценты
                round(remaining_debt, 2)  # Остаток долга
            ))

            # переходим к следующему месяцу
            m += 1
            # если долг выплачен, то выходим из цикла
            if remaining_debt <= 0:
                break

        return schedule
    # вывод в интерфейс
    def update_table(self, schedule):
        # количество строк в таблице по размеру нашего списка
        self.payment_tabel.setRowCount(len(schedule))
        # строка, данные
        for row_idx, row_data in enumerate(schedule):
            # колонка, конкретное число
            for col_idx, value in enumerate(row_data):
                # форматирование чисел
                if isinstance(value, (int, float)) and col_idx > 0:
                    # пробелы между тысячами
                    display_text = f"{value:,.2f}".replace(",", " ")
                else:
                    display_text = str(value)
                # создание ячейки таблицы
                item = QTableWidgetItem(display_text)
                # выравниваем текст по центру
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # втсавляем ячейку на определенное место
                self.payment_tabel.setItem(row_idx, col_idx, item)
    # чекбокс досрочки
    def handle_early_check(self, state):
        # если галочка снята
        if state == 0:
            # очищаем поле  и убираем красную подстветку
            self.early_sum_input.clear()
            self.clear_single_error(self.early_sum_input)
    # тоже самое с комиссиями
    def handle_comm_check(self, state):
        if state == 0:
            self.comm_val_input.clear()
            self.clear_single_error(self.comm_val_input)
    # метод очистки всех результатов расчета на экране
    def clear_all_data(self):
        super().clear_all_data()
        # обнуляем метки с результатами
        self.res_payment.setText("0.00 руб.")
        self.res_total.setText("0.00 руб.")
        self.res_overpay.setText("0.00 руб.")


if __name__ == "__main__":
    # основной объеткт приложения Qt
    app = QApplication(sys.argv)
    # создаем экземпляр класса с интерфейсом
    window = interface_user()
    window.showMaximized()
    # запускаем циклл обработки и корректный выход из программы
    sys.exit(app.exec())