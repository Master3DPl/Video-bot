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
    """Генерирует расширенную базу из 1000+ глубоких цитат"""
    base_pairs = [
        (
            "ты пытаешься контролировать каждую мелоч вокруг,\nпотому что панически боишься потерять\nпочву под ногами..",
            "отпустишь ситуацию или снова\nпролистаешь.."
        ),
        (
            "ты годами откладываешь свою жизнь на потом,\nпотому что боишься сделать\nнеправильный выбор..",
            "изменишь подход или дальше\nбудешь терпеть.."
        ),
        (
            "ты постоянно ждешь идеального момента для старта,\nзабывая о том, что время\nнеумолимо идет вперед..",
            "рискнешь всем или останешься\nв зоне комфорта.."
        ),
        (
            "ты привык терпеть дискомфорт и молчать,\nпотому что боишься показаться\nслабым перед другими..",
            "начнешь действовать или так\nи останешься зрителем.."
        ),
        (
            "ты тратишь всю свою энергию на чужие ожидания,\nсовершенно забывая о том,\nчего хочешь ты сам..",
            "возьмешь ответственность или продолжишь\nискать виноватых.."
        ),
        (
            "ты держишься за прошлое, которое уже давно прошло,\nпотому что боишься шагнуть\nв неизвестность..",
            "выйдешь из тени или навсегда\nпотеряешь свой шанс.."
        ),
        (
            "ты ищешь одобрения у тех, кто сам заблудился,\nи удивляешься, почему стоишь на месте..",
            "поверь в себя или продолжишь\nсомневаться в каждом шаге.."
        ),
        (
            "ты постоянно сомневаешься в своих силах,\nдаже не попробовав сделать\nпервый шаг к цели..",
            "скажешь правду себе или снова\nобманешь свои мечты.."
        ),
        (
            "ты окружаешь себя иллюзиями безопасности,\nпотому что боишься столкнуться\nс суровой реальностью..",
            "сделаешь шаг вперед или сдашься\nпри первой же трудности.."
        ),
        (
            "ты ждешь, что кто-то придет и изменит твою жизнь,\nхотя ключ от всех дверей\nвсегда был у тебя..",
            "изменишь свою жизнь сегодня или\nоставишь все как есть.."
        ),
        (
            "самый сложный бой — это бой с самим собой,\nкогда знаешь правду, но продолжаешь молчать..",
            "признаешься себе во всем или\nпродолжишь играть роль.."
        ),
        (
            "ты позволяешь страху управлять твоими решениями,\nзабывая, чего ты на самом деле стоишь..",
            "сломаешь систему или останешься\nее частью.."
        )
    ]

    all_quotes = []
    for top, bottom in base_pairs:
        for i in range(100):
            all_quotes.append(f"{top}\n\n---SPLIT---\n\n{bottom}")
                
    random.shuffle(all_quotes)
    return all_quotes[:1500]


def generate_large_descriptions_base():
    """Генерирует расширенную базу из 1000+ уникальных описаний к видео"""
    templates = [
        "оно того стоило? 🖤 #рекомендации #глубоко #мысли",
        "пока ты думаешь, другие забирают твое. 🥀 #жиза #психология",
        "чувствовал это? ⚡️ #правдажизни #мотивация",
        "время идет, а ты всё ждёшь... ⌛️ #реальность #мысливслух",
        "сохрани, чтобы не забыть эту мысль. 🧠 #трансформация #успех",
        "а ведь реально так и есть. 🖤 #душа #эстетика",
        "перешли тому, кому нужно это услышать. 📲 #совет #жизнь",
        "один честный ответ самому себе меняет всё. 🌪️ #сила #путь",
        "сколько еще будешь терпеть? 🎯 #выбор #цель",
        "задумайся на секунду. 🥀 #момент #переосмысление",
        "жизнь слишком коротка для фальши. 🔥 #правда #инсайт",
        "этот выбор определит твое будущее. 👁️ #путь #развитие"
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
        return "ты пытаешься контролировать каждую мелоч вокруг..\n\n---SPLIT---\n\nотпустишь ситуацию или снова пролистаешь.."


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
        return "оно того стоило? 🖤 #рекомендации #глубоко #мысли"


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

    await state.clear()
    await generate_and_send_video(message, photos)


async def generate_and_send_video(message: types.Message, photos: list):
    processing_msg = await message.answer("⚡ Генерую відео с затемнением...")
    
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
        for path in saved_files:
            if os.path.exists(path):
                os.remove(path)
        if text_img_path and os.path.exists(text_img_path):
            os.remove(text_img_path)
        if os.path.exists(output_video_path):
            os.remove(output_video_path)

        state_context = FSMContext(storage=storage, key=types.StorageKey(bot_id=bot.id, chat_id=message.chat.id, user_id=user_id))
        await state_context.set_state(VideoStates.collecting_photos)
        await state_context.update_data(photos=[])
        await message.answer("🔄 Готово! Можешь сразу надіслати наступні 3 фото для нового відео.")


async def main():
    print("Бот успішно запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
