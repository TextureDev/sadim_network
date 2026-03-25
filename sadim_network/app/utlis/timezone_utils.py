from datetime import datetime
import pytz


class Timezone:

    @staticmethod
    def get_time_and_greeting(tz_name="Africa/Tripoli"):

        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)

        current_time = now.strftime("%Y-%m-%d")

        hour = now.hour

        if 5 <= hour < 12:
            greeting = "صباح الخير"
        elif 12 <= hour < 17:
            greeting = "مساء النور"
        else:
            greeting = "مساء الخير"

        return current_time, greeting