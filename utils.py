import math
import time

def humanbytes(size):
    # Converts bytes to human readable format (e.g., 1024 -> 1 KB)
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def time_formatter(seconds):
    # Converts seconds to HH:MM:SS
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s") if seconds else "")
    return tmp

async def progress_for_pyrogram(current, total, ud_type, message, start):
    # Displays a progress bar in the Telegram message
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = time_formatter(milliseconds=elapsed_time)
        estimated_total_time = time_formatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \n**Progress**: {2}%\n".format(
            ''.join(["●" for i in range(math.floor(percentage / 5))]),
            ''.join(["○" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "**{0}**: {1}/{2}\n**Speed**: {3}/s\n**ETA**: {4}".format(
            ud_type,
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(f"{ud_type}\n{tmp}")
        except:
            pass
          
