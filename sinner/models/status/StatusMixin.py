import locale
import shutil
import sys

from colorama import Back, Fore

from sinner.models.status.Mood import Mood


class StatusMixin:
    enable_emoji: bool = False
    emoji: str

    @staticmethod
    def set_position(position: tuple[int, int] | None = None) -> None:
        if position is not None:
            y = position[0]
            x = position[1]
            if y < 0 or x < 0:
                terminal_size = shutil.get_terminal_size()
                lines, columns = terminal_size.lines, terminal_size.columns
                if y < 0:
                    y += lines
                if x < 0:
                    x += columns

            sys.stdout.write(f"\033[{y};{x}H")

    @staticmethod
    def restore_position(position: tuple[int, int] | None = None) -> None:
        if position is not None:
            sys.stdout.write("\033[u")

    @staticmethod
    def is_emoji_supported() -> bool:
        try:
            return locale.getpreferredencoding().lower() == "utf-8"
        except Exception:
            return False

    def update_status(self, message: str, caller: str | None = None, mood: Mood = Mood.GOOD, emoji: str | None = None, position: tuple[int, int] | None = None) -> None:
        """
        Print the specified status message
        :param message: the status message text
        :param caller: the caller class name, None to a current class name
        :param mood: the mood of the message (good, bad, neutral)
        :param emoji: prefix emoji. Note: emoji may be skipped, if not supported in the current terminal
        :param position: output position as (line, column). Negative values interprets as positions from the bottom/right
        side of the console. Skip to print status at the current cursor position.
        """
        if self.enable_emoji:
            if emoji is None:
                emoji = self.emoji
        else:
            emoji = ''
        if caller is None:
            caller = self.__class__.__name__
        self.set_position(position)
        sys.stdout.write(f'{emoji}{mood}{caller}: {message}{Back.RESET}{Fore.RESET}')
        if position is None:
            sys.stdout.write("\n")
        self.restore_position(position)


