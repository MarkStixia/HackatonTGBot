import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TOKEN)
search_url = 'https://ru.stackoverflow.com/search?q='
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    config.currentpages[user_id] = "main"
    bot.send_message(
        chat_id=message.chat.id,
        text="Добро пожаловать в наш бот который упростит работу с StackOverflow",
        reply_markup=config.GetMainKeyboard()
    )

@bot.message_handler(commands=['search'])
def search_command(message):
    user_id = message.from_user.id
    config.currentpages[user_id] = "search"
    command_parts = message.text.split(' ', 1)
    if len(command_parts) > 1:
        search_query = command_parts[1]
        search(message, query=search_query)
    else:
        (bot.reply_to(message, "Пожалуйста, введите текст для поиска после команды /search."))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, text="Вы можете управлять ботом при помощи следующих комманд или кнопок:\n/start - перезапуск бота\n/search ЗАПРОС - поиск по Stackoverflow\n/help - выводит данное меню помощи",
                          reply_markup=config.GetGoBackKeyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'search':
        config.currentpages[user_id] = "search"
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Введите ваш запрос", reply_markup=config.GetGoBackKeyboard())

    elif call.data == 'next_question':
        if user_id in user_data:
            current_index = user_data[user_id]['current_index']
            questions = user_data[user_id]['questions']
            if current_index + 1 < len(questions):
                user_data[user_id]['current_index'] += 1
                user_data[user_id]['current_answer_index'] = 0
                update_question(chat_id, message_id, user_data[user_id]['current_index'])
            else:
                bot.answer_callback_query(call.id, "Это последний вопрос.")
        else:
            bot.answer_callback_query(call.id, "Сначала выполните поиск вопросов.")

    elif call.data == 'prev_question':
        if user_id in user_data:
            current_index = user_data[user_id]['current_index']
            if current_index > 0:
                user_data[user_id]['current_index'] -= 1
                user_data[user_id]['current_answer_index'] = 0
                update_question(chat_id, message_id, user_data[user_id]['current_index'])
            else:
                bot.answer_callback_query(call.id, "Это первый вопрос.")
        else:
            bot.answer_callback_query(call.id, "Сначала выполните поиск вопросов.")

    elif call.data == 'show_answer':
        if user_id in user_data:
            current_index = user_data[user_id]['current_index']
            answers = user_data[user_id]['answers']
            current_answer_index = user_data[user_id].get('current_index', 0)

            if current_answer_index < len(answers):
                if(current_answer_index == 0):
                    send_answer(chat_id, message_id, answers[current_answer_index])
                else:
                    send_answer(chat_id, message_id, answers[current_answer_index + 1])
            else:
                bot.answer_callback_query(call.id, "Ответ для этого вопроса отсутствует.")
        else:
            bot.answer_callback_query(call.id, "Сначала выполните поиск вопросов.")

    elif call.data == 'next_answer':
        if user_id in user_data:
            current_index = user_data[user_id]['current_index']
            answers = user_data[user_id]['answers']
            current_answer_index = user_data[user_id].get('current_answer_index', 0)

            if current_answer_index + 1 < len(answers):
                user_data[user_id]['current_answer_index'] += 1
                send_answer(chat_id, message_id, answers[user_data[user_id]['current_answer_index']])
            else:
                bot.answer_callback_query(call.id, "Это последний ответ.")
        else:
            bot.answer_callback_query(call.id, "Сначала выполните поиск вопросов.")

    elif call.data == 'back':
        current_index = user_data[user_id]['current_index']
        update_question(chat_id, message_id, current_index)

    elif call.data == 'menu':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Добро пожаловать в наш бот который упростит работу с StackOverflow",
                              reply_markup=config.GetMainKeyboard())
    elif call.data == 'help':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Вы можете управлять ботом при помощи следующих комманд или кнопок:\n/start - перезапуск бота\n/search ЗАПРОС - поиск по Stackoverflow\n/help - выводит данное меню помощи",
                              reply_markup=config.GetGoBackKeyboard())

@bot.message_handler(content_types=['voice', 'photo', 'sticker', 'video', 'document'])
def handle_media(message):
    bot.send_message(message.chat.id,"Никакого медиа!")

@bot.message_handler()
def main(message):
    user_id = message.from_user.id
    if config.currentpages.get(user_id) == "search":
       search(message, "")

def search(message, query):
    if(query != ""):
        message.text = query

    user_id = message.from_user.id
    loadmessage = bot.send_message(message.chat.id, "⌛️ Загрузка данных...")
    query = message.text.replace(' ', '+').replace('+', '%2b')
    url = search_url + query
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('div', class_='s-post-summary js-post-summary')
    answers = []
    questions = []

    for result in results:
        question_element = result.find('a', class_='s-link')
        if not question_element:
            continue

        question_text = question_element.get_text(strip=True)

        answers_count_element = result.find('div', class_='s-post-summary--stats-item',
                                            title=lambda x: x and 'ответов' in x)
        if answers_count_element:
            answers_count = int(answers_count_element.find('span', class_='s-post-summary--stats-item-number').text)
            if answers_count == 0:
                continue

        thread_link_element = result.find('a', class_='s-link')
        if thread_link_element:
            thread_link = thread_link_element['href']
            thread_url = 'https://ru.stackoverflow.com' + thread_link
            thread_html = fetch_page(thread_url)
            thread_soup = BeautifulSoup(thread_html, 'html.parser')

            answer_elements = thread_soup.find_all('div', class_='answercell post-layout--right')

            for answer_element in answer_elements:
                answer_text_element = answer_element.find('div', class_='s-prose js-post-body')
                if answer_text_element:
                    answer_text = answer_text_element.get_text(strip=False)
                    answers.append((thread_url, answer_text))

        questions.append(question_text)

    bot.delete_message(message_id=loadmessage.message_id, chat_id=loadmessage.chat.id)
    if questions:
        user_data[user_id] = {
            'questions': questions,
            'answers': answers,
            'current_index': 0,
            'current_answer_index': 0
        }
        send_question(message.chat.id, 0)
        return

    bot.send_message(message.chat.id, "Результаты не найдены.")

def send_question(chat_id, question_index):
    user_id = chat_id
    question = user_data[user_id]['questions'][question_index]
    bot.send_message(chat_id=chat_id, text=f"❓ Вопрос:\n{question}", reply_markup=config.GetQuestionKeyboard())

def update_question(chat_id, message_id, question_index):
    user_id = chat_id
    question = user_data[user_id]['questions'][question_index]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                          text=f"❓ Вопрос:\n{question}", reply_markup=config.GetQuestionKeyboard())

def send_answer(chat_id, message_id, answer):
    thread_url, answer_text = answer
    answer_text = answer_text[:3000]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"💬 Ответ:\n{answer_text}\n\n[🔗 Источник]({thread_url})",
                          parse_mode='Markdown', reply_markup=config.GetAnswerInlineKeyboard())

def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе страницы: {e}")
        return None

bot.polling(non_stop=True)
