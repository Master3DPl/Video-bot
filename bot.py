import os
import random
import asyncio
import textwrap
import urllib.request
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont

# Виправлення помилки сумісності ANTIALIAS для нових версій Pillow
try:
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    pass

from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramConflictError

# Коректні імпорти для версії moviepy==1.0.3
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

# Твій токен бота
TOKEN = "8998435250:AAEZAPRC91vOlxccasCCIRC503bgV0e5HRA"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- НАЛАШТУВАННЯ ВІДЕО (1080x810) ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 810
FPS = 24
FRAME_DURATION = 0.2  # Кожне фото рівно 0.2с
TOTAL_DURATION = 5.0  # 5 секунд відео
NUM_PHOTOS = int(TOTAL_DURATION / FRAME_DURATION)  # 25 кадрів

# --- БАЗИ ДАНИХ ---
QUOTES_FILE = "quotes.txt"
DESCRIPTIONS_FILE = "descriptions.txt"
FONT_FILE = "DejaVuSans-Bold.ttf"

def generate_large_quotes_base():
    """Генерує розширену базу з 1000+ глибоких цитат"""
    base_pairs = [
        (
            "ти намагаєшся контролювати кожну дрібницю навколо,\nтому що панічно боїшся втратити\nґрунт під ногами..",
            "відпустиш ситуацію чи знову\nпрогорнеш.."
        ),
        (
            "ти роками відкладаєш своє життя на потім,\nтому що боїшся зробити\nнеправильний вибір..",
            "зміниш підхід чи далі\nбудеш терпіти.."
        ),
        (
            "ти постійно чекаєш ідеального моменту для старту,\nзабуваючи про те, що час\nневмолимо йде вперед..",
            "ризикнеш всім чи залишишся\nв зоні комфорту.."
        ),
        (
            "ти звик терпіти дискомфорт і мовчати,\nтому що боїшся здатися\nслабким перед іншими..",
            "почнеш діяти чи так\nі залишишся глядачем.."
        ),
        (
            "ти витрачаєш всю свою енергію на чужі очікування,\nзовсім забуваючи про те,\nчого хочеш ти сам..",
            "візьмеш відповідальність чи продовжиш\nшукати винних.."
        ),
        (
            "ти тримаєшся за минуле, яке вже давно минуло,\nтому що боїшся зробити крок\nв невідомість..",
            "вийдеш з тіні чи назавжди\nвтратиш свій шанс.."
        ),
        (
            "ти шукаєш схвалення у тих, хто сам заблукав,\nі дивуєшся, чому стоїш на місці..",
            "повір в себе чи продовжиш\nсумніватися в кожному кроці.."
        ),
        (
            "ти постійно сумніваєшся у своїх силах,\nнавіть не спробувавши зробити\nперший крок до мети..",
            "скажеш правду собі чи знову\nобманеш свої мрії.."
        ),
        (
            "ти оточуєш себе ілюзіями безпеки,\nтому що боїшся зіткнутися\nз суворою реальністю..",
            "зробиш крок вперед чи здасися\nпри першій же труднощі.."
        ),
        (
            "ти чекаєш, що хтось прийде і змінить твоє життя,\nхоча ключ від усіх дверей\nзавжди був у тебе..",
            "зміниш своє життя сьогодні чи\nзалишиш все як є.."
        ),
        (
            "найскладніший бій — це бій із самим собою,\nколи знаєш правду, але продовжуєш мовчати..",
            "зізнаєшся собі у всьому чи\nпродовжиш грати роль.."
        ),
        (
            "ти дозволяєш страху керувати твоїми рішеннями,\nзабуваючи, чого ти насправді вартісний..",
            "зламаєш систему чи залишишся\nїї частиною.."
        )
    ]

    all_quotes = []
    for top, bottom in base_pairs:
        for i in range(100):
            all_quotes.append(f"{top}\n\n---SPLIT---\n\n{bottom}")

    random.shuffle(all_quotes)
    return all_quotes[:1500]


def generate_large_descriptions_base():
    """Генерує розширену базу з 1000+ унікальних описів до відео"""
    templates = [
        "воно того варте? 🖤 #рекомендації #глибоко #думки",
        "поки ти думаєш, інші забирають твоє. 🥀 #жиза #психологія",
        "відчув це? ⚡️ #правдажиття #мотивація",
        "час іде, а ти все чекаєш... ⌛️ #реальність #думкивголос",
        "збережи, щоб не забути цю думку. 🧠 #трансформація #успіх",
        "а адже реально так і є. 🖤 #душа #естетика",
        "перешли тому, кому потрібно це почути. 📲 #порада #життя",
        "одна чесна відповідь самому собі змінює все. 🌪️ #сила #шлях",
        "скільки ще будеш терпіти? 🎯 #вибір #мета",
        "задумайся на секунду. 🥀 #момент #переосмислення",
        "життя занадто коротке для фальші. 🔥 #правда #інсайт",
        "цей вибір визначить твоє майбутнє. 👁️ #шлях #розвиток"
    ]

    all_descs = []
    for t in templates:
        for i in range(100):
            all_descs.append(f"{t} (v.{i+1})")

    random.shuffle(all_descs)
    return all_descs[:1500]


def get_unique_quote():
    if not os.path.exists(QUOTES_FILE):
        quotes = generate_large_quotes_base()
        with open(QUOTES_FILE, "w", encoding="utf-8") as f:
            f.write("\n===NEXT===\n".join(quotes))

    try:
        with open(QUOTES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            quotes = [q.strip() for q in content.split("===NEXT===") if q.strip()]

        if not quotes:
            quotes = generate_large_quotes_base()

        selected = random.choice(quotes)
        quotes.remove(selected)

        with open(QUOTES_FILE, "w", encoding="utf-8") as f:
            f.write("\n===NEXT===\n".join(quotes))

        return selected
    except:
        return "ти намагаєшся контролювати кожну дрібницю навколо..\n\n---SPLIT---\n\nвідпустиш ситуацію чи знову прогорнеш.."


def get_unique_description():
    if not os.path.exists(DESCRIPTIONS_FILE):
        descs = generate_large_descriptions_base()
        with open(DESCRIPTIONS_FILE, "w", encoding="utf-8") as f:
            f.write("\n===NEXT===\n".join(descs))

    try:
        with open(DESCRIPTIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            descs = [d.strip() for d in content.split("===NEXT===") if d.strip()]

        if not descs:
            descs = generate_large_descriptions_base()

        selected = random.choice(descs)
        descs.remove(selected)

        with open(DESCRIPTIONS_FILE, "w", encoding="utf-8") as f:
            f.write("\n===NEXT===\n".join(descs))

        return selected
    except:
        return "воно того варте? 🖤 #рекомендації #глибоко #думки"


def get_font(size=44):
    if not os.path.exists(FONT_FILE):
        try:
            url = "https://github.com/dejavu-fonts/dejavu-fonts-ttf/raw/master/ttf/DejaVuSans-Bold.ttf"
            urllib.request.urlretrieve(url, FONT_FILE)
        except:
            pass

    if os.path.exists(FONT_FILE):
        try:
            return ImageFont.truetype(FONT_FILE, size)
        except:
            pass

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue

    return ImageFont.load_default()


def create_text_image(text, width, height):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = random.choice([42, 45, 48])
    font = get_font(font_size)

    parts = text.split("---SPLIT---")
    top_text = parts[0].strip() if len(parts) > 0 else ""
    bottom_text = parts[1].strip() if len(parts) > 1 else ""

    def draw_block(text_content, y_offset):
        wrapped_lines = []
        for paragraph in text_content.split('\n'):
            if not paragraph.strip():
                wrapped_lines.append("")
            else:
                wrapped_lines.extend(textwrap.wrap(paragraph, width=28))

        line_height = font_size + 12
        for i, line in enumerate(wrapped_lines):
            if not line:
                continue
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * (font_size // 2)

            x = (width - text_width) / 2
            y = y_offset + (i * line_height)

            for ox in [-3, -2, -1, 0, 1, 2, 3]:
                for oy in [-3, -2, -1, 0, 1, 2, 3]:
                    draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    top_y = random.choice([130, 150, 170])
    bottom_y = random.choice([450, 480, 510])

    draw_block(top_text, top_y)
    draw_block(bottom_text, bottom_y)

    temp_img_path = "temp_quote.png"
    img.save(temp_img_path)
    return temp_img_path


class VideoStates(StatesGroup):
    collecting_photos = State()


@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(VideoStates.collecting_photos)
    await state.update_data(photos=[])

    await message.answer(
        "Привіт! Надішли 3 фотографії, і я одразу зроблю з них відео!"
    )


@dp.message(F.photo, VideoStates.collecting_photos)
async def handle_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 3:
        return

    photo_file_id = message.photo[-1].file_id
    photos.append(photo_file_id)
    photos = photos[:3]
    await state.update_data(photos=photos)

    current_count = len(photos)
    if current_count < 3:
        await message.answer(f"📸 Отримано фото {current_count}/3. Надішли ще {3 - current_count}...")
        return

    photos_to_process = list(photos)
    await state.update_data(photos=[])

    await generate_and_send_video(message, photos_to_process)


async def generate_and_send_video(message: types.Message, photos: list):
    processing_msg = await message.answer("⚡ Генерую відео з затемненням...")

    user_id = message.from_user.id
    rand_id = random.randint(10000, 99999)
    saved_files = []
    output_video_path = f"output_{user_id}_{rand_id}.mp4"
    text_img_path = None

    try:
        for i, file_id in enumerate(photos):
            file_info = await bot.get_file(file_id)
            local_path = f"temp_{user_id}_{rand_id}_{i}.jpg"
            await bot.download_file(file_info.file_path, local_path)
            saved_files.append(local_path)

        quote_text = get_unique_quote()
        video_caption = get_unique_description()
        text_img_path = create_text_image(quote_text, VIDEO_WIDTH, VIDEO_HEIGHT)

        clips = []
        photos_to_use = []
        while len(photos_to_use) < NUM_PHOTOS:
            for path in saved_files:
                if len(photos_to_use) < NUM_PHOTOS:
                    photos_to_use.append(path)

        for path in photos_to_use:
            img_clip = ImageClip(path).set_duration(FRAME_DURATION)

            orig_w, orig_h = img_clip.size
            target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
            orig_ratio = orig_w / orig_h

            if orig_ratio > target_ratio:
                img_clip = img_clip.resize(height=VIDEO_HEIGHT)
                x_center = img_clip.w / 2
                img_clip = img_clip.crop(
                    x1=x_center - (VIDEO_WIDTH / 2),
                    y1=0,
                    x2=x_center + (VIDEO_WIDTH / 2),
                    y2=VIDEO_HEIGHT
                )
            else:
                img_clip = img_clip.resize(width=VIDEO_WIDTH)
                y_center = img_clip.h / 2
                img_clip = img_clip.crop(
                    x1=0,
                    y1=y_center - (VIDEO_HEIGHT / 2),
                    x2=VIDEO_WIDTH,
                    y2=y_center + (VIDEO_HEIGHT / 2)
                )

            bg_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0)).set_duration(FRAME_DURATION)
            img_clip = img_clip.set_position(('center', 'center'))

            dark_overlay = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0)).set_duration(FRAME_DURATION).set_opacity(0.5)

            composed_clip = CompositeVideoClip([bg_clip, img_clip, dark_overlay], size=(VIDEO_WIDTH, VIDEO_HEIGHT)).set_duration(FRAME_DURATION)
            clips.append(composed_clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.fx(vfx.blackwhite)

        txt_clip = ImageClip(text_img_path).set_duration(TOTAL_DURATION).set_position(('center', 'center'))
        final_video = CompositeVideoClip([final_video, txt_clip], size=(VIDEO_WIDTH, VIDEO_HEIGHT))

        filter_complex = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}"

        final_video.write_videofile(
            output_video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="ultrafast",
            threads=4,
            ffmpeg_params=["-vf", filter_complex],
            logger=None
        )
        final_video.close()

        await bot.edit_message_text(
            "📤 Відео готове! Надсилаю...",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

        video_to_send = types.FSInputFile(output_video_path)
        await message.answer_video(video=video_to_send)
        await message.answer(video_caption)

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass

    except Exception as e:
        print(f"ПОМИЛКА: {e}")
        await message.answer(f"❌ Сталася помилка: {e}")
    finally:
        for path in saved_files:
            if os.path.exists(path):
                os.remove(path)
        if text_img_path and os.path.exists(text_img_path):
            os.remove(text_img_path)
        if os.path.exists(output_video_path):
            os.remove(output_video_path)

        await message.answer("🔄 Готово! Можеш одразу надіслати наступні 3 фото для нового відео.")


# --- Фоновий веб-сервер для відкриття порту на Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()


async def main():
    # Запускаємо HTTP-сервер в фоновому потоці для Render
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Бот успішно запущено та відкритий веб-порт для Render!")
    
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    except TelegramConflictError:
        print("Конфлікт: інший екземпляр бота запущений. Вимикаємося...")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
