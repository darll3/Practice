from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFrame, QLabel, QLineEdit, \
    QHBoxLayout, QGridLayout, QButtonGroup, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QComboBox, \
    QCheckBox, QSpinBox, QMessageBox, QToolTip
from PyQt6.QtCore import Qt, QLocale, QRegularExpression, QPoint
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QRegularExpressionValidator, QColor
import sys


class Program(QMainWindow):
    def __init__(self):
        super().__init__()

        #валидация для дробных чисел
        self.numeric_validator = QDoubleValidator(0.0, 1000000000.0, 2)
        # вид записи чтоб был стандартным без e и тд
        self.numeric_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        #валидация ввода точки, а не запятой
        self.numeric_validator.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

        # создаем кнопки и применяем к ним дизайн
        self.init_ui()
        self.apply_styles()
        #все поля ввода
        self.all_inputs = [
            self.sum_input, self.date_input, self.term_input,
            self.rate_input, self.rate_input_fixed,
            self.early_sum_input, self.early_date_input, self.comm_val_input,
            self.custom_day_input
        ]
        # кроме полей даты и срока, устанавливаем валидацию на ввод только чисел
        for field in self.all_inputs:
            if field not in [self.date_input, self.term_input, self.early_date_input]:
                field.setValidator(self.numeric_validator)

                # Проверка на наличие запятых и точек с запятой во всем тексте
                field.textChanged.connect(lambda _, f=field: self.check_invalid_symbols(f))
                # Проверка, чтобы ввод не начинался с разделителя
                field.textChanged.connect(lambda _, f=field: self.validate_input_start(f))

            #Снимаем красную штуку, как только пользователь начал вводить чтото
            field.textChanged.connect(lambda _, f=field: self.clear_field_error(f))
        # для срока кредита разрешен вво только целых числе от 1 до 600
        self.term_input.setValidator(QIntValidator(1, 600))

        #привязываем функции к кнопкам
        self.btn_clear.clicked.connect(self.clear_all_data)
        self.check_early.stateChanged.connect(self.toggle_sections)
        self.check_comm.stateChanged.connect(self.toggle_sections)
        self.btn_fixed.clicked.connect(self.on_rate_type_changed)
        self.btn_variable.clicked.connect(self.on_rate_type_changed)
        self.btn_add_rate.clicked.connect(self.add_rate_row)

        #блокируем поля досрочки и комиссиий
        self.toggle_sections()
        #делаем сразу фиксировануую ставку для удобства ну и так как она чаще всего выбирается
        self.btn_fixed.setChecked(True)
        # это для видимости полей при выборе ставки
        self.on_rate_type_changed()
        # белая таблица сразу
        self.clear_table_to_default()

    def check_invalid_symbols(self, widget):
        text = widget.text()

        # Список символов, которые мы хотим ловить
        invalid_symbols = [',', ';']

        # Проверяем, есть ли хоть один запрещенный символ в тексте
        for char in invalid_symbols:
            if char in text:
                # Очищаем текст от этих символов
                new_text = text.replace(char, '')
                widget.setText(new_text)

                # Показываем красивый ToolTip как в вашем стиле
                QToolTip.showText(
                    widget.mapToGlobal(QPoint(20, widget.height())),
                    f"Ошибка: используйте точку вместо '{char}'",
                    widget
                )
                break  # Прерываем цикл после первой найденной ошибки

    # функция которая запреает начинать ввод с точки или запятой
    def validate_input_start(self, widget):
        text = widget.text()
        if text.startswith('.') or text.startswith(','):
            # убирает точку и запятую
            widget.setText(text.lstrip('.,'))
            #сообщение об ошибке
            QToolTip.showText(
                widget.mapToGlobal(QPoint(0, widget.height())),
                "Число не может начинаться с разделителя",
                widget
            )
    # созадение кнопки со знаком вопроса
    def create_help_button(self, text):
        btn = QPushButton("?")
        btn.setFixedSize(22, 22)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("helpButton")
        # убираем всплывающую подсказку (она появляется если долго держать курсор на кнопке)
        btn.setToolTip("")
        # а вот тут создаем подсказку по клику
        btn.clicked.connect(lambda: QToolTip.showText(
            btn.mapToGlobal(QPoint(25, 0)),
            text,
            btn
        ))

        return btn

    # делает сразу 10 пустых строк, для обозначения что это таблица
    def clear_table_to_default(self):
        self.payment_tabel.setRowCount(10)
        # проходимся по строкам и столбцам
        for i in range(10):
            for j in range(self.payment_tabel.columnCount()):
                # создаем объект, те ячейку и записываем в нее пустую строку
                item = QTableWidgetItem("")
                item.setBackground(QColor("white"))
                # созданную ячейку кладем в таблицу на пересечение строки и столбца
                self.payment_tabel.setItem(i, j, item)

    # очищаем ошибки
    def clear_all_errors(self):
        # создаем список с основными полями
        all_to_check = [self.sum_input, self.term_input, self.rate_input,
                        self.rate_input_fixed, self.date_input, self.custom_day_input]
        # передается пустой список для того чтобы убрать красную обводку
        self.highlight_errors([])

    # кнопка очистить
    def clear_all_data(self):
        # проходим по списку всех текстовых полей
        for field in self.all_inputs:
            field.clear()
        # снимаем красные поля
        self.clear_all_errors()
        # и делаем таблицу по дефолту
        self.clear_table_to_default()

        # очистка полей в части результат
        self.res_payment.clear()
        self.res_total.clear()
        self.res_overpay.clear()

        # сброс чекбоксов
        self.check_early.setChecked(False)
        self.check_comm.setChecked(False)

        # сброс для групп кнопок
        for group in [self.type_group, self.day_group, self.furst_pay_group, self.early_group, self.freq_group,
                      self.comm_group]:
            # врменно отключаем эксклюзивность, те не иметь нажатых кнопок
            group.setExclusive(False)
            # для каждой кнопки из групп
            for btn in group.buttons():
                # выкдючаем нажатие кнопки
                btn.setChecked(False)
            # подключаем эксклюзивность в группу
            group.setExclusive(True)

        # сразу ставим рабочую кнопку ставки фиксированная
        self.btn_fixed.setChecked(True)
        # управление полями в зависимости от ставки
        self.on_rate_type_changed()

    # чекбоксы
    def toggle_sections(self):
        # досрочка,проверка на то, стоит ли галочка
        is_early = self.check_early.isChecked()
        # создаем список всех полей которые находяся в досрочке
        early_widgets = [
            self.early_sum_input, self.btn_reduce_sum, self.btn_reduce_term,
            self.btn_once, self.btn_monthly, self.btn_yearly, self.early_date_input
        ]
        # проходим по списку элементов
        for w in early_widgets:
            # включаем или выключаем элемент
            w.setEnabled(is_early)
            # если галочки нет, то убираем красную рамку
            if not is_early:
                self.clear_field_error(w)

        # чекбокс у комиссии
        is_comm = self.check_comm.isChecked()
        comm_widgets = [
            self.btn_comm_once, self.btn_comm_month,
            self.comm_val_input, self.comm_unit_combo
        ]
        for w in comm_widgets:
            w.setEnabled(is_comm)
            if not is_comm:
                self.clear_field_error(w)

    def init_ui(self):
        self.setWindowTitle("Калькулятор")
        #добавляем скролл
        self.main_scroll = QScrollArea()
        # содеожимое подстраивается под размер
        self.main_scroll.setWidgetResizable(True)
        # минус лишняя рамка вокруг скорола
        self.main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        # деламе его главным элементом окна
        self.setCentralWidget(self.main_scroll)
        # создаем виджет, как подложку под все остальное и добалвяем ее внутрь скрола
        self.scroll_content = QWidget()
        self.main_scroll.setWidget(self.scroll_content)
        # создаем горизонтальеый макет и делаем там отступы
        self.main_layout = QHBoxLayout(self.scroll_content)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        # отступы между левой и правой панелью
        self.main_layout.setSpacing(20)

        # левая колонка и внутри отсупы между параметрами досрочкой и комиссией
        self.left_panel = QVBoxLayout()
        self.left_panel.setSpacing(15)

        # создаем главое окно параметра
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setFixedWidth(500)

        layout = QVBoxLayout(self.main_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Параметры кредита")
        header.setObjectName("Header")
        layout.addWidget(header)

        layout.addWidget(QLabel('Сумма кредита'))
        self.sum_input = QLineEdit()
        self.sum_input.setPlaceholderText("0.00")
        layout.addWidget(self.sum_input)

        layout.addWidget(QLabel("Дата выдачи"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self.date_input.setInputMask("99.99.9999")
        layout.addWidget(self.date_input)

        layout.addWidget(QLabel("Срок кредита"))
        term_layout = QHBoxLayout()
        self.term_input = QLineEdit()

        self.term_unit_combo = QComboBox()
        self.term_unit_combo.addItems(["мес.", "лет"])
        self.term_unit_combo.setFixedWidth(80)

        term_layout.addWidget(self.term_input)
        term_layout.addWidget(self.term_unit_combo)
        layout.addLayout(term_layout)

        layout.addWidget(QLabel("Ставка кредита"))
        rate_buttons = QHBoxLayout()
        self.btn_fixed = QPushButton("Фиксированная")
        self.btn_variable = QPushButton("Изменяемая")
        self.btn_fixed.setCheckable(True)
        self.btn_variable.setCheckable(True)
        self.rate_group = QButtonGroup(self)
        self.rate_group.addButton(self.btn_fixed)
        self.rate_group.addButton(self.btn_variable)
        rate_buttons.addWidget(self.btn_fixed)
        rate_buttons.addWidget(self.btn_variable)
        layout.addLayout(rate_buttons)

        #ставки
        self.rate_container = QFrame()
        self.rate_container.setObjectName("RateContainer")
        self.rate_container.hide()

        self.rate_changes_layout = QVBoxLayout(self.rate_container)
        self.rate_changes_layout.setSpacing(0)
        self.rate_changes_layout.setContentsMargins(0, 0, 0, 0)

        first_row = QHBoxLayout()
        first_row.setContentsMargins(15, 10, 15, 10)
        lbl_start = QLabel("Дата выдачи")
        lbl_start.setFixedWidth(120)
        self.rate_input = QLineEdit()
        self.rate_input.setPlaceholderText("0.00%")
        self.rate_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        first_row.addWidget(lbl_start)
        first_row.addWidget(self.rate_input)
        first_row.addSpacing(40)
        self.rate_changes_layout.addLayout(first_row)

        layout.addWidget(self.rate_container)

        self.btn_add_rate = QPushButton("ДОБАВИТЬ")
        self.btn_add_rate.setObjectName("addRateBtn")
        self.btn_add_rate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_rate.hide()
        layout.addWidget(self.btn_add_rate)

        #поле для фикс ставки
        self.rate_input_fixed = QLineEdit()
        self.rate_input_fixed.setPlaceholderText("%")
        layout.addWidget(self.rate_input_fixed)

        type_label_layout = QHBoxLayout()
        type_label_layout.addWidget(QLabel("Вид платежа"))
        self.help_type = self.create_help_button(
            "Аннуитетный — платежи равны весь срок.\nДифференцированный — платеж уменьшается к концу.")
        type_label_layout.addWidget(self.help_type)
        type_label_layout.addStretch()
        layout.addLayout(type_label_layout)
        type_buttons = QHBoxLayout()
        self.btn_annity = QPushButton("Aннуитетный")
        self.btn_diff = QPushButton("Дифференцированный")
        self.btn_annity.setCheckable(True)
        self.btn_diff.setCheckable(True)
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.btn_annity)
        self.type_group.addButton(self.btn_diff)

        type_buttons.addWidget(self.btn_annity)
        type_buttons.addWidget(self.btn_diff)
        layout.addLayout(type_buttons)

        day_label_layout = QHBoxLayout()
        day_label_layout.addWidget(QLabel("День платежей"))
        self.help_day = self.create_help_button(
            "Выберите дату ежемесячного списания.\nЕсли день 31-й, а в месяце 30 дней — спишется в последний день.")
        day_label_layout.addWidget(self.help_day)
        day_label_layout.addStretch()
        layout.addLayout(day_label_layout)
        # создаем сетку
        day_grid = QGridLayout()

        self.btn_issue_day = QPushButton("В день выдачи\nкредита")
        self.btn_issue_day.setObjectName("smallBtn")
        self.btn_issue_day.setCheckable(True)

        self.btn_last_day = QPushButton("В последний день\nмесяца")
        self.btn_last_day.setObjectName("smallBtn")
        self.btn_last_day.setCheckable(True)

        self.custom_day_input = QLineEdit()
        self.custom_day_input.setPlaceholderText("Свой день")
        self.custom_day_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.custom_day_input.setFixedWidth(100)
        self.custom_day_input.setMaxLength(2)
        # ввод чисел от 1 до 31 РЕШИТЬ ЧТОТО С ЭТИМ
        reg_exp = QRegularExpression("^(?:[1-9]|[12][0-9]|3[01])$")
        validator = QRegularExpressionValidator(reg_exp, self.custom_day_input)
        self.custom_day_input.setValidator(validator)
        # создаем группу кнопок и делаем так чтобы была нажата только одна
        self.day_group = QButtonGroup(self)
        self.day_group.addButton(self.btn_issue_day)
        self.day_group.addButton(self.btn_last_day)
        self.day_group.setExclusive(True)

        #если начали писать сввой день
        self.custom_day_input.textChanged.connect(
            lambda: [
                self.day_group.setExclusive(False),# разрешаем гурппе иметь ниодной нажатой кнопки
                [b.setChecked(False) for b in self.day_group.buttons()], #если были выбраны кнопки, то снимаем с них выделения
                self.day_group.setExclusive(True) #включаем режим выбора одной кнопки
            ] if self.custom_day_input.text() else None) #делаем только в том случае если поле не пустое
        # если кликнули на любую кнопку в группе,то очищаем поле свой день
        self.day_group.buttonClicked.connect(lambda: self.custom_day_input.clear())
        # размещаем кнопки и поле ввода в сетке
        day_grid.addWidget(self.btn_issue_day, 0, 0)
        day_grid.addWidget(self.btn_last_day, 0, 1)
        day_grid.addWidget(self.custom_day_input, 0, 2)
        # добавляем сетку в макет
        layout.addLayout(day_grid)

        layout.addWidget(QLabel("Первый платеж"))
        furst_pay_buttons = QHBoxLayout()
        self.btn_interest_only = QPushButton("Только проценты")
        self.btn_full_pay = QPushButton("Проценты и часть\nосновного долга")
        self.btn_full_pay.setObjectName("smallBtn")
        furst_pay_buttons.addWidget(self.btn_interest_only)
        furst_pay_buttons.addWidget(self.btn_full_pay)
        self.btn_interest_only.setCheckable(True)
        self.btn_full_pay.setCheckable(True)
        self.furst_pay_group = QButtonGroup(self)
        self.furst_pay_group.addButton(self.btn_interest_only)
        self.furst_pay_group.addButton(self.btn_full_pay)
        layout.addLayout(furst_pay_buttons)

        #Досрочное погашение
        self.early_pay_frame = QFrame()
        self.early_pay_frame.setObjectName("MainFrame")
        self.early_pay_frame.setFixedWidth(500)
        early_layout = QVBoxLayout(self.early_pay_frame)
        early_layout.setContentsMargins(20, 20, 20, 20)
        early_layout.setSpacing(10)

        early_header = QLabel("Досрочное погашение")
        early_header.setObjectName("Header")

        #чекбокс досрочки
        self.check_early = QCheckBox()
        self.check_early.setFixedSize(25, 25)

        early_header_layout = QHBoxLayout()
        early_header_layout.addWidget(early_header)
        self.help_early = self.create_help_button(
            "Снижение платежа — сумма в месяц станет меньше.\nСнижение срока — быстрее закроете кредит.")
        early_header_layout.addWidget(self.help_early)
        early_header_layout.addWidget(self.check_early)
        early_header_layout.addStretch()
        early_layout.addLayout(early_header_layout)

        early_layout.addWidget(QLabel("Сумма досрочного платежа"))
        self.early_sum_input = QLineEdit()
        self.early_sum_input.setPlaceholderText("0.00")
        early_layout.addWidget(self.early_sum_input)

        early_layout.addWidget(QLabel("Тип погашения"))
        early_type_btns = QHBoxLayout()
        self.btn_reduce_sum = QPushButton("Снизить платёж")
        self.btn_reduce_term = QPushButton("Снизить срок")
        self.btn_reduce_sum.setCheckable(True)
        self.btn_reduce_term.setCheckable(True)
        self.early_group = QButtonGroup(self)
        self.early_group.addButton(self.btn_reduce_sum)
        self.early_group.addButton(self.btn_reduce_term)
        early_type_btns.addWidget(self.btn_reduce_sum)
        early_type_btns.addWidget(self.btn_reduce_term)
        early_layout.addLayout(early_type_btns)

        early_layout.addWidget(QLabel("Частота"))
        freq_btns = QHBoxLayout()
        self.btn_once = QPushButton("Единовременно")
        self.btn_monthly = QPushButton("Раз в месяц")
        self.btn_yearly = QPushButton("Раз в год")
        self.freq_group = QButtonGroup(self)
        for btn in [self.btn_once, self.btn_monthly, self.btn_yearly]:
            # делаем кнопки кликапельными
            btn.setCheckable(True)
            # добавляем в гурппу
            self.freq_group.addButton(btn)
            # и добавляем в горизональный ряд а потом в общий макет
            freq_btns.addWidget(btn)
        early_layout.addLayout(freq_btns)

        early_layout.addWidget(QLabel("Дата"))
        self.early_date_input = QLineEdit()
        self.early_date_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self.early_date_input.setInputMask("99.99.9999")
        early_layout.addWidget(self.early_date_input)

        #Комиссии
        self.comm_frame = QFrame()
        self.comm_frame.setObjectName("MainFrame")
        self.comm_frame.setFixedWidth(500)
        comm_layout = QVBoxLayout(self.comm_frame)
        comm_layout.setContentsMargins(20, 20, 20, 20)
        comm_layout.setSpacing(10)

        comm_header = QLabel("Комиссии")
        comm_header.setObjectName("Header")

        #чекбокс комиссий
        self.check_comm = QCheckBox()
        self.check_comm.setFixedSize(25, 25)

        comm_header_layout = QHBoxLayout()
        comm_header_layout.addWidget(comm_header)
        self.help_comm = self.create_help_button(
            "Единовременная — платится один раз при выдаче.\nЕжемесячная — добавляется к каждому платежу.")
        comm_header_layout.addWidget(self.help_comm)
        comm_header_layout.addWidget(self.check_comm)
        comm_header_layout.addStretch()
        comm_layout.addLayout(comm_header_layout)

        comm_type_btns = QHBoxLayout()
        self.btn_comm_once = QPushButton("Единовременная")
        self.btn_comm_month = QPushButton("Ежемесячная")
        self.btn_comm_once.setCheckable(True)
        self.btn_comm_month.setCheckable(True)
        self.comm_group = QButtonGroup(self)
        self.comm_group.addButton(self.btn_comm_once)
        self.comm_group.addButton(self.btn_comm_month)
        comm_type_btns.addWidget(self.btn_comm_once)
        comm_type_btns.addWidget(self.btn_comm_month)
        comm_layout.addLayout(comm_type_btns)

        comm_inputs = QHBoxLayout()
        self.comm_val_input = QLineEdit()
        self.comm_val_input.setPlaceholderText("Введите значение")
        self.comm_unit_combo = QComboBox()
        self.comm_unit_combo.addItems(["руб", "%"])
        self.comm_unit_combo.setFixedWidth(80)
        comm_inputs.addWidget(self.comm_val_input)
        comm_inputs.addWidget(self.comm_unit_combo)
        comm_layout.addLayout(comm_inputs)

        #собираем в левую панель
        self.left_panel.addWidget(self.main_frame)
        self.left_panel.addWidget(self.early_pay_frame)
        self.left_panel.addWidget(self.comm_frame)

        #Кнопки расчитать и очистить
        result_buttons = QHBoxLayout()
        self.btn_calculate = QPushButton("Рассчитать")
        self.btn_calculate.setObjectName("calculateBTN")
        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.setObjectName("clearBTN")
        result_buttons.addWidget(self.btn_calculate)
        result_buttons.addWidget(self.btn_clear)
        self.left_panel.addLayout(result_buttons)
        self.left_panel.addStretch()

        #Фрейм для результатов
        self.result_frame = QFrame()
        self.result_frame.setObjectName("resultFrame")
        self.result_frame.setFixedHeight(200)
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(20, 20, 20, 20)

        self.result_title = QLabel("Результат:")
        self.result_title.setObjectName("Result")
        result_layout.addWidget(self.result_title)

        def create_result_row(text):
            row = QHBoxLayout()
            label = QLabel(text)
            display = QLineEdit()
            display.setReadOnly(True)
            display.setFixedWidth(700)
            row.addWidget(label)
            row.addWidget(display)

            result_layout.addLayout(row)
            return display

        self.res_payment = create_result_row("Ежемесячный платеж:")
        self.res_total = create_result_row("Общая сумма платежа:")
        self.res_overpay = create_result_row("Переплата:")

        #Фрейм с графиком платежей
        self.table_frame = QFrame()
        self.table_frame.setObjectName("tabelname")
        table_layout = QVBoxLayout(self.table_frame)

        table_header = QLabel("График платежей")
        table_header.setObjectName("tabelheader")
        # выравниваем по середине
        table_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(table_header)

        self.payment_tabel = QTableWidget()
        # скрываем номера строк
        self.payment_tabel.verticalHeader().setVisible(False)
        # запрещаем печаать текст в ячейках
        self.payment_tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # создаем 5 колоно и пишем у них названия
        self.payment_tabel.setColumnCount(5)
        self.payment_tabel.setHorizontalHeaderLabels(["Дата", "Платеж", "Осн.долг", "Проценты", "Остаток"])

        #строчки в таблице
        # берем названия и растягиваем колонки во всю ширину таблицы
        header = self.payment_tabel.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # добавляем таблицу в макет и создаем сразу 10 пустых строк
        table_layout.addWidget(self.payment_tabel)
        self.payment_tabel.setRowCount(10)

        #правая колонка
        self.right_panel = QVBoxLayout()
        self.right_panel.addWidget(self.result_frame)
        self.right_panel.addWidget(self.table_frame)

        #Сборка левой и правой пнели
        self.main_layout.addLayout(self.left_panel)
        self.main_layout.addLayout(self.right_panel)

    def apply_styles(self):
        self.setStyleSheet("""
            #MainFrame, #resultFrame, #tabelname {
                background-color: #E2F9E8;
                border-radius: 20px;
                border: 2.5px solid #74c43f;
            }

            #Header, #tabelheader, #Result {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }

            #calculateBTN {
                background: #90f59a;
                min-height: 40px;
                font-weight: bold;
                border-radius: 10px;
            }

            #clearBTN {
                background: #f66565;
                color: white;
                min-height: 40px;
                font-weight: bold;
                border-radius: 10px;
            }

            #helpButton {
                border-radius: 11px;
                background-color: #D1D1E9;
                color: #4A4A4A;
                font-weight: bold;
                border: none;
                padding: 0px;
            }

            #helpButton:hover {
                background-color: #B1B1D9;
            }
            
            QToolTip {
                background-color: #E2F9E8;
                color: #333333;
                border: 1.5px solid #74c43f;
                padding: 8px;
                font-size: 13px;
            }

            QLabel {
                font-size: 14px;
                color: black;
                margin-top: 5px;
                background: transparent;
            }

            QLineEdit, QPushButton, QComboBox, QSpinBox {
                border: none;
                border-radius: 10px;
                background-color: white;
                padding: 5px;
                font-size: 14px;
                color: #333;
                min-height: 25px;
            }

            QLineEdit[error="true"] {
                border: 2px solid #f66565;
                background-color: #fff0f0;
            }

            QPushButton:checked {
                background-color: #B4F0C9;
                color: black;
                font-weight: bold;
            }

            QPushButton#smallBtn {
                font-size: 10px;
            }

            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #74c43f;
                border-radius: 2px;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: #90f59a;
                border: 2px solid #2e7d32;
            }
            QTableWidget{
                background-color: transparent;
                border: none;
                gridline-color: transparent;
                alternate-background-color: #F0F0F0;
                outline: none;
            }
            QTableWidget::item {
                background-color: white;
                color: black;
                padding: 10px;
                border: none;
            }
            QHeaderView::section {
                background-color: #B4F0C9;
                border: none;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
                color: black;
            }

            QLineEdit:disabled, QPushButton:disabled, QComboBox:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
            QMessageBox {
                background-color: #E2F9E8;
                border: 2px solid #74c43f;
            }
            QMessageBox QPushButton {
                background-color: #90f59a;
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: bold;
            }

        """)

    # для изменения ставки
    def add_rate_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(15, 10, 15, 10)

        date_edit = QLineEdit()
        date_edit.setPlaceholderText("ДД.ММ.ГГГГ")
        date_edit.setInputMask("99.99.9999")
        # убираем красную рамку если пользователь начал чтото писать
        date_edit.textChanged.connect(lambda: self.clear_field_error(date_edit))

        rate_edit = QLineEdit()
        rate_edit.setPlaceholderText("0.00%")
        # текст по центру поля, разрешаем писать только числа
        rate_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate_edit.setValidator(self.numeric_validator)
        # очищаем поля при изменении текста и ставим проверку на ввод, чтобы не начинался с . или ,
        rate_edit.textChanged.connect(lambda: self.clear_field_error(rate_edit))
        rate_edit.textChanged.connect(lambda: self.validate_input_start(rate_edit))

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(30, 30)
        # если нажимаем удаляем весь row_widget
        del_btn.clicked.connect(lambda: row_widget.deleteLater())
        # добавляем все элементы и добавляем в вертикальный макет
        row_layout.addWidget(date_edit)
        row_layout.addWidget(rate_edit)
        row_layout.addWidget(del_btn)
        self.rate_changes_layout.addWidget(row_widget)

    #кнопка добавить только при изменяемой ставке
    def on_rate_type_changed(self):
        # нажата ли сейчас кнопка изменяемая
        is_var = self.btn_variable.isChecked()
        # если да, то показываем контейнер с датами и ставкой и кнопку добавить
        self.rate_container.setVisible(is_var)
        self.btn_add_rate.setVisible(is_var)
        # поле для фиксированной показываем если не нажата изменяемая ставка
        self.rate_input_fixed.setVisible(not is_var)
        # если вернулся к фиксированной ставке
        if not is_var:
            #Очищает строки и возвращает фиксированную ставку
            # идем с конца списка,удалаем все кроме первой строк
            for i in reversed(range(1, self.rate_changes_layout.count())):
                # берем строку под номером i и если она нашлась то удаляем
                widget = self.rate_changes_layout.itemAt(i).widget()
                if widget: widget.deleteLater()

    def highlight_errors(self, widgets):
        #проходим по всем полям ввола
        for field in self.all_inputs:
            # сначала убираем ошибку, после застявляем забыть как выглядим поле и заново делаем проверку
            field.setProperty("error", "false")
            field.style().unpolish(field)
            field.style().polish(field)

        #проходим по полям в которых есть ошибка
        for widget in widgets:
            # ошибка да, сбрасываем внешний вид и ставми красную рамку
            widget.setProperty("error", "true")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    #снимает красную подстветку с поля
    def clear_field_error(self, field):
        if field.property("error") == "true":
            # если поле свойство ошибка да, меняем на нет
            field.setProperty("error", "false")
            # сбрасываем стиль и обновляем
            field.style().unpolish(field)
            field.style().polish(field)
            # принудительно перерисовыаем поле, без задержек
            field.update()
