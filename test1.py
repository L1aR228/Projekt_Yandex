import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout,
    QWidget, QPushButton, QLineEdit, QMessageBox, QListWidget, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer


class Database:
    """Класс для управления базой данных вопросов."""

    def __init__(self, db_name="quiz.db"):
        self.connection = None
        self.cursor = None
        self.connect(db_name)

    def connect(self, db_name):
        """Соединение с базой данных для вопросов."""
        try:
            self.connection = sqlite3.connect(db_name)
            self.cursor = self.connection.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            sys.exit(1)

    def create_tables(self):
        """Создание таблицы, если она не существует."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    correct_answer TEXT NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать таблицы: {str(e)}")
            sys.exit(1)

    def insert_question(self, question, answer):
        """Добавление вопроса в базу данных."""
        try:
            self.cursor.execute("INSERT INTO questions (question, correct_answer) VALUES (?, ?)", (question, answer))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось добавить вопрос: {str(e)}")

    def get_questions(self):
        """Получение всех вопросов из базы данных."""
        try:
            self.cursor.execute("SELECT id, question, correct_answer FROM questions")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось получить вопросы: {str(e)}")
            return []

    def delete_question(self, question_id):
        """Удаление вопроса из базы данных по ID."""
        try:
            self.cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось удалить вопрос: {str(e)}")

    def clear_questions(self):
        """Очистка всех вопросов из базы данных и сброс автоинкремента."""
        try:
            self.cursor.execute("DELETE FROM questions")
            self.connection.commit()
            self.reset_id()  # Сброс автоинкремента после удаления всех вопросов
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось очистить вопросы: {str(e)}")

    def reset_id(self):
        """Сброс автоинкрементируемого id."""
        try:
            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='questions'")
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось сбросить id: {str(e)}")

    def delete_all_questions(self):
        """Удаление всех вопросов из базы данных и сброс счетчика ID."""
        self.cursor.execute("DELETE FROM questions")
        self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='questions'")  # Сбрасываем автоинкрементный счётчик
        self.connection.commit()

    def close(self):
        """Закрытие соединения с базой данных."""
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()


class ResultsDatabase:
    """Класс для управления базой данных результатов."""

    def __init__(self, db_name="results.db"):
        self.connection = None
        self.cursor = None
        self.connect(db_name)

    def connect(self, db_name):
        """Соединение с базой данных для результатов."""
        try:
            self.connection = sqlite3.connect(db_name)
            self.cursor = self.connection.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных результатов: {str(e)}")
            sys.exit(1)

    def create_tables(self):
        """Создание таблицы для результатов, если она не существует."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    score INTEGER NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать таблицу результатов: {str(e)}")
            sys.exit(1)

    def insert_result(self, name, score):
        """Сохранение результата ученика в базе данных."""
        try:
            self.cursor.execute("INSERT INTO results (name, score) VALUES (?, ?)", (name, score))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось сохранить результат: {str(e)}")

    def get_results(self):
        """Получение всех результатов из базы данных."""
        try:
            self.cursor.execute("SELECT name, score FROM results")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось получить результаты: {str(e)}")
            return []

    def clear_results(self):
        """Очистка базы данных результатов."""
        try:
            self.cursor.execute("DELETE FROM results")
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось очистить результаты: {str(e)}")

    def close(self):
        """Закрытие соединения с базой данных результатов."""
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()


class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Программа для проверки знаний")
        self.setGeometry(100, 100, 400, 300)

        self.database = Database()
        self.results_database = ResultsDatabase()
        self.test_duration = 60

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        student_button = QPushButton("Ученик")
        teacher_button = QPushButton("Учитель")

        student_button.clicked.connect(self.name_lastname)
        teacher_button.clicked.connect(self.ask_password)

        layout.addWidget(student_button)
        layout.addWidget(teacher_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def name_lastname(self):
        """Запрос имени и фамилии ученика"""
        name, ok = QInputDialog.getText(self, "Имя", "Введите свое имя:")
        if ok and name:
            self.show_student_window(name)
        else:
            QMessageBox.warning(self, "Ошибка", "Вы не ввели имя.")

    def show_student_window(self, student_name):
        """Показать окно ученика."""
        self.student_window = StudentWindow(self.database, self.results_database, self, self.test_duration,
                                            student_name)
        self.student_window.show()
        self.close()

    def ask_password(self):
        """Запрос пароля для доступа к окну учителя"""
        password, ok = QInputDialog.getText(self, "Пароль", "Введите пароль:")

        if ok and password == "1":
            self.show_admin_window()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")

    def show_admin_window(self):
        """Показать окно для учителя."""
        self.teacher_window = Admin(self.database, self)
        self.teacher_window.show()
        self.close()


class StudentWindow(QWidget):
    def __init__(self, database, results_database, parent, duration, student_name):
        super().__init__()
        self.database = database
        self.results_database = results_database
        self.parent = parent
        self.student_name = student_name
        self.quiz_ended = False
        self.duration = duration

        self.setWindowTitle("Ученик")
        self.setGeometry(100, 100, 400, 300)

        self.question_label = QLabel(self)
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.answer_input = QLineEdit(self)
        self.submit_button = QPushButton("Ответить", self)
        self.back_button = QPushButton("Назад", self)

        self.correct_answer_counter = QLabel("Правильные ответы: 0", self)
        self.correct_answer_counter.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.correct_answer_counter.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.timer_label = QLabel(f"Оставшееся время: {self.format_time(self.duration)}", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.initUI()

        self.score = 0
        self.questions = self.database.get_questions()
        self.current_question_index = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        if self.questions:
            self.load_question()
        else:
            QMessageBox.warning(self, "Ошибка", "Нет доступных вопросов для теста!")

    def format_time(self, seconds):
        """Форматирование времени"""
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02}:{seconds:02}"

    def update_timer(self):
        if self.duration > 0:
            self.duration -= 1
            self.timer_label.setText(f"Оставшееся время: {self.format_time(self.duration)}")
        else:
            if not self.quiz_ended:
                self.quiz_ended = True
                self.end_quiz()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(self.correct_answer_counter)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.question_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.back_button)
        self.submit_button.clicked.connect(self.check_answer)
        self.back_button.clicked.connect(self.go_back)
        self.setLayout(layout)

    def load_question(self):
        """Загрузка следующего вопроса из базы данных со номером вопроса"""
        if self.current_question_index < len(self.questions):
            question_number = self.current_question_index + 1
            self.question_label.setText(
                f"Вопрос {question_number}: {self.questions[self.current_question_index][1]}")  # Текст вопроса с номером
            self.answer_input.clear()  # Очищаем поле ввода
        else:
            self.end_quiz()  # Если вопросы закончились, завершить викторину

    def check_answer(self):
        """Проверка ответа пользователя"""
        answer = self.answer_input.text()
        correct_answer = self.questions[self.current_question_index][2] if self.current_question_index < len(
            self.questions) else None

        if answer == '':
            QMessageBox.information(self, "Ошибка!", 'Вы не ввели ответ ')
        elif correct_answer:
            if answer.strip().lower() == correct_answer.strip().lower():
                self.score += 1
                self.correct_answer_counter.setText(f"Правильные ответы: {self.score}")
            else:
                QMessageBox.warning(self, "Неправильно!", f"Правильный ответ: {correct_answer}")

            self.current_question_index += 1
            self.load_question()

    def end_quiz(self):
        """Завершение викторины и вывод результата"""
        grade = self.calculate_grade(self.score)
        self.results_database.insert_result(self.student_name, self.score)
        QMessageBox.information(self, "Викторина завершена!",
                                f"Ваш результат: {self.score} из {len(self.questions)}.\nВаша оценка: {grade}.")
        self.close()
        self.parent.show()

    def calculate_grade(self, score):
        """Подсчёт оценки на основе баллов"""
        total_questions = len(self.questions)
        if total_questions == 0:
            return "Нет вопросов"

        if score >= total_questions * 0.75:
            return "Отлично\n оценка 5"
        elif score >= total_questions * 0.5:
            return "Хорошо\n оценка 4"
        elif score >= total_questions * 0.25:
            return "Удовлетворительно\n оценка 3"
        else:
            return "Неудовлетворительно\n оценка 2"

    def go_back(self):
        """Возврат к главному окну"""
        self.parent.show()
        self.close()


class Admin(QWidget):
    """Окно для учителя с административными правами."""

    def __init__(self, database, parent):
        super().__init__()
        self.database = database
        self.parent = parent

        self.setWindowTitle("Админ")
        self.setGeometry(100, 100, 400, 300)
        self.submit_button = QPushButton("Проверить результаты учеников", self)
        self.delete_button1 = QPushButton("Изменение вопросов", self)
        self.set_time_button = QPushButton("Установить время теста", self)
        self.back_button = QPushButton("Назад", self)

        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна учителя"""
        layout = QVBoxLayout()
        layout.addWidget(self.submit_button)
        layout.addWidget(self.set_time_button)
        layout.addWidget(self.delete_button1)
        layout.addWidget(self.back_button)

        self.setLayout(layout)

        self.back_button.clicked.connect(self.go_back)
        self.delete_button1.clicked.connect(self.show_correct_window)
        self.set_time_button.clicked.connect(self.ask_time)
        self.submit_button.clicked.connect(self.show_results_window)

    def show_results_window(self):
        """Показать окно с результатами учеников."""
        self.results_window = ResultsWindow(self.database, self.parent.results_database, self)
        self.results_window.show()
        self.close()

    def go_back(self):
        """Возврат к главному окну."""
        self.parent.show()
        self.close()

    def show_correct_window(self):
        """Показать окно учителя."""
        self.correct_window = TeacherWindow(self.database, self)
        self.correct_window.show()
        self.close()

    def ask_time(self):
        """Запрос времени для теста у учителя"""
        time, ok = QInputDialog.getInt(self, "Установить время теста", "Введите время в минутах:", value=1, min=1)
        if ok:
            duration = time * 60
            self.parent.test_duration = duration
            QMessageBox.information(self, "Успех", f"Время теста установлено на {time} минут(ы).")


class ResultsWindow(QWidget):
    def __init__(self, database, results_database, parent):
        super().__init__()
        self.database = database
        self.results_database = results_database
        self.parent = parent
        self.setWindowTitle("Результаты учеников")
        self.setGeometry(100, 100, 400, 300)
        self.results_list = QListWidget(self)
        self.back_button = QPushButton("Назад", self)
        self.clear_button = QPushButton("Очистка", self)
        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна с результатами"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Результаты учеников:"))
        layout.addWidget(self.results_list)
        layout.addWidget(self.back_button)
        layout.addWidget(self.clear_button)
        self.setLayout(layout)
        self.load_results()
        self.back_button.clicked.connect(self.go_back)
        self.clear_button.clicked.connect(self.clear)

    def load_results(self):
        """Загрузка результатов учеников из базы данных"""
        self.results_list.clear()
        results = self.results_database.get_results()
        for name, score in results:
            self.results_list.addItem(f"Имя: {name}, Очки: {score}")

    def clear(self):
        """Очистка результатов в базе данных и вопросов"""
        self.results_database.clear_results()
        self.database.clear_questions()  # Очищаем вопросы и сбрасываем автоинкремент
        self.load_results()
        self.parent.show()
        self.close()

    def go_back(self):
        """Возврат к окну администратора"""
        self.parent.show()
        self.close()


class TeacherWindow(QWidget):
    """Окно для управления вопросами."""

    def __init__(self, database, parent):
        super().__init__()
        self.database = database
        self.parent = parent

        self.setWindowTitle("Учитель")
        self.setGeometry(100, 100, 400, 300)

        self.question_input = QLineEdit(self)
        self.answer_input = QLineEdit(self)
        self.submit_button = QPushButton("Добавить вопрос", self)
        self.delete_button = QPushButton("Удалить вопрос", self)
        self.delete_all_button = QPushButton("Удалить все вопросы", self)  # Новая кнопка
        self.back_button = QPushButton("Назад", self)
        self.question_list = QListWidget(self)

        self.initUI()

        # Загрузка вопросов из базы данных
        self.load_questions()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна учителя"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите вопрос:"))
        layout.addWidget(self.question_input)
        layout.addWidget(QLabel("Введите правильный ответ:"))
        layout.addWidget(self.answer_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(QLabel("Список вопросов:"))
        layout.addWidget(self.question_list)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.delete_all_button)  # Добавление новой кнопки удаления всех вопросов
        layout.addWidget(self.back_button)

        self.submit_button.clicked.connect(self.add_question)
        self.delete_button.clicked.connect(self.delete_question)
        self.delete_all_button.clicked.connect(self.delete_all_questions)  # Подключение к новой функции
        self.back_button.clicked.connect(self.go_back)

        self.setLayout(layout)

    def delete_all_questions(self):
        """Удаление всех вопросов из базы данных."""
        try:
            self.database.delete_all_questions()  # Вызов метода удаления всех вопросов
            QMessageBox.information(self, "Успех!", "Все вопросы успешно удалены!")
            self.load_questions()  # Обновляем список вопросов
        except Exception as e:
            QMessageBox.critical(self, "Ошибка!", f"Не удалось удалить все вопросы: {str(e)}")

    def load_questions(self):
        """Загрузка вопросов из базы данных в список"""
        try:
            self.question_list.clear()
            questions = self.database.get_questions()
            for question in questions:
                self.question_list.addItem(f"{question[0]}: {question[1]}")  # Добавление ID и текста вопроса
        except Exception as e:
            QMessageBox.critical(self, "Ошибка!", f"Не удалось загрузить вопросы: {str(e)}")

    def add_question(self):
        """Добавление вопроса в базу данных."""
        question = self.question_input.text()
        answer = self.answer_input.text()

        if question and answer:
            try:
                self.database.insert_question(question, answer)
                QMessageBox.information(self, "Успех!", "Вопрос добавлен!")
                self.question_input.clear()
                self.answer_input.clear()
                self.load_questions()  # Обновляем список вопросов
            except Exception as e:
                QMessageBox.critical(self, "Ошибка!", f"Не удалось добавить вопрос: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка!", "Пожалуйста, заполните оба поля.")

    def delete_question(self):
        """Удаление выбранного вопроса из базы данных"""
        selected_items = self.question_list.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            question_id = int(selected_item.text().split(":")[0])  # Извлечение ID из текста
            try:
                self.database.delete_question(question_id)
                QMessageBox.information(self, "Успех!", "Вопрос успешно удален!")
                self.load_questions()  # Обновляем список вопросов
            except Exception as e:
                QMessageBox.critical(self, "Ошибка!", f"Не удалось удалить вопрос: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка!", "Пожалуйста, выберите вопрос для удаления.")

    def go_back(self):
        """Возврат к главному окну."""
        self.parent.show()  # Показываем родительское окно (главное окно)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    quiz_app = QuizApp()
    quiz_app.show()
    sys.exit(app.exec())
