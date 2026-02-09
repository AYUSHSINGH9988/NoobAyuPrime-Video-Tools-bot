import math
import time

# File size ko human readable banane ke liye
def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

# Time ko format karne ke liye
def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

# Main Progress Bar Function
async def progress_for_pyrogram(current, total, ud_type, message, start, file_name=""):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        # Percentage Calculation
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = time_formatter(milliseconds=elapsed_time)
        estimated_total_time = time_formatter(milliseconds=estimated_total_time)

        # Progress Bar Design
        progress = "[{0}{1}] \n**Progress**: {2}%\n".format(
            ''.join(["●" for i in range(math.floor(percentage / 10))]),
            ''.join(["○" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))
        
        # Output String
        tmp = progress + "**📁 File**: `{0}`\n**⚡ Speed**: {1}/s\n**🚀 Done**: {2} of {3}\n**⏳ ETA**: {4}\n**🛡️ Status**: {5}".format(
            file_name,
            humanbytes(speed),
            humanbytes(current),
            humanbytes(total),
            estimated_total_time if estimated_total_time != '' else "0 s",
            ud_type
        )
        try:
            await message.edit(
                text="{}\n\n{}".format(ud_type, tmp)
            )
        except:
            pass
          
