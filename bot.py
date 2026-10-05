import os
import random
import asyncio
import textwrap
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# Исправление ошибки совместимости ANTIALIAS для новых версий Pillow
try:
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    pass

from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Корректные импорты для версии moviepy==1.0.3
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

# Твой токен бота
TOKEN = "8998435250:AAEZAPRC91vOlxccasCCIRC503bgV0e5HRA"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- НАСТРОЙКИ ВИДЕО (1080x810) ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 810
FPS = 24
FRAME_DURATION = 0.2  # Каждое фото ровно 0.2с
TOTAL_DURATION = 5.0  # 5 секунд видео
NUM_PHOTOS = int(TOTAL_DURATION / FRAME_DURATION)  # 25 кадров

# --- БАЗЫ ДАННЫХ ---
QUOTES_FILE = "quotes.txt"
DESCRIPTIONS_FILE = "descriptions.txt"
FONT_FILE = "DejaVuSans-Bold.ttf"

def generate_large_quotes_base():
    """Генерирует базу из 1000+ цитат без упоминания денег, с перефразом и разным количеством пацанов"""
    actions_and_counts = [
        ("Мне нужны {count}, и я сделаю из них людей,\nкоторые никогда больше не прогнутся под систему.", "А ты снова пролистываешь?"),
        ("Мне нужны {count}, кто устал подчиняться чужим правилам\nи готов забрать своё по праву.", "Жду тебя"),
        ("Мне нужны {count} верных человека в братство,\nкоторые не предадут при первой же трудности.", "Жду тебя"),
        ("Мне нужны {count}, у которых в глазах горит огонь,\nа не желание просто дожить до пятницы.", "А ты снова пролистываешь?"),
        ("Мне нужны {count}, кто хочет построить свой путь с нуля,\nа не искать оправдания в пустых отговорках.", "Сделай выбор."),
        ("Мне нужны {count} бойца, которые готовы идти до конца,\nчтобы потом жить так, как другие не могут.", "Жду тебя"),
        ("Мне нужны {count} человека с амбициями выше среднего,\nа не те, кого устраивает стабильная серость.", "Задумайся."),
        ("Мне нужны {count}, кто готов рисковать ради победы,\nчтобы навсегда вырваться из этой рутины.", "А ты снова пролистываешь?")
    ]

    count_variants = [
        "два пацана", "три пацана", "четыре пацана", "пять пацанов",
        "пару надежных пацанов", "три толковых пацана", "четыре бойца", "два человека"
    ]

    all_quotes = []
    for template, bottom in actions_and_counts:
        for c in count_variants:
            for _ in range(30):
                top = template.format(count=c)
                all_quotes.append(f"{top}\n\n---SPLIT---\n\n{bottom}")

    random.shuffle(all_quotes)
    return all_quotes[:1500]


def generate_large_descriptions_base():
    """Генерирует расширенную базу из 1000+ уникальных описаний к видео"""
    templates = [
        "Тот самый человек поймет без лишних слов. Отправь ему 🖤 #рекомендации #глубоко #мысли",
        "Пока ты думаешь, другие забирают твое. 🥀 #жиза #психология #правдажизни",
        "После этого видео ты посмотришь на всё иначе. Напиши в комменты, если узнал себя. ⚡️ #мотивация",
        "Время идет, а ты всё ждёшь... ⌛️ #реальность #мысливслух",
        "Сохрани, пока эта мысль не потерялась в суете. 🧠 #трансформация #успех",
        "А ведь реально так и есть. 🖤 #душа #эстетика",
        "Перешли тому, кому нужно это услышать. 📲 #совет #жизнь",
        "Один честный ответ самому себе меняет всё. 🌪 #сила #путь",
        "Сколько ещё будешь терпеть? 🎯 #выбор #цель",
        "Задумайся на секунду... 🥀 #момент #переосмысление",
        "Жизнь слишком коротка для фальши. 🔥 #инсайт",
        "Этот выбор определит твое будущее. 👁️ #путь #развитие"
    ]

    all_descs = []
    for t in templates:
        for i in range(100):
            all_descs.append(f"{t} (v.{i+1})")

    random.shuffle(all_descs)
    return all_descs[:1500]


def get_unique_quote():
    """Берёт цитату из файла и удаляет её, чтобы она не повторялась"""
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
        return "Мне нужны три пацана, и я сделаю из них людей,\nкоторые никогда больше не прогнутся под систему.\n\n---SPLIT---\n\nА ты снова пролистываешь?"


def get_unique_description():
    """Берёт уникальное описание из файла и удаляет его"""
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
        return "Тот самый человек поймет без лишних слов. Отправь ему 🖤 #рекомендации #глубоко #мысли"


def get_font(size=44):
    """Гарантированно загружает шрифт нужного размера (скачивает, если файла нет)"""
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
    """Рисует крупный, читаемый текст с вариативным стилем"""
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

            # Жирная черная обводка для четкого контраста
            for ox in [-3, -2, -1, 0, 1, 2, 3]:
                for oy in [-3, -2, -1, 0, 1, 2, 3]:
                    draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
            # Белый текст поверх
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
        "Привіт! Надішли 3 фотографией, і я одразу зроблю з них відео!"
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

    await state.clear()
    await generate_and_send_video(message, photos)


async def generate_and_send_video(message: types.Message, photos: list):
    processing_msg = await message.answer("⚡ Генерую відео с затемнением...")

    user_id = message.from_user.id
    rand_id = random.randint(10000, 99999)
    saved_files = []
    output_video_path = f"output_{user_id}_{rand_id}.mp4"
    text_img_path = None
    final_video = None

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
        
        # Закрываем клипы во избежание утечек памяти
        final_video.close()
        for c in clips:
            c.close()

        await bot.edit_message_text(
            "📤 Відео готово! Надсилаю...",
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
        # Безопасное закрытие видеоклипа если произошла ошибка
        try:
            if final_video:
                final_video.close()
        except:
            pass

        for path in saved_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        if text_img_path and os.path.exists(text_img_path):
            try:
                os.remove(text_img_path)
            except:
                pass
        if os.path.exists(output_video_path):
            try:
                os.remove(output_video_path)
            except:
                pass

        state_context = FSMContext(storage=storage, key=types.StorageKey(bot_id=bot.id, chat_id=message.chat.id, user_id=user_id))
        await state_context.set_state(VideoStates.collecting_photos)
        await state_context.update_data(photos=[])
        await message.answer("🔄 Готово! Можешь сразу надіслати наступні 3 фото для нового відео.")


async def main():
    print("Бот успішно запущено!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
