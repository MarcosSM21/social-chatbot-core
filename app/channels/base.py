from typing import Protocol

class ChannelAdapter(Protocol):
    def run(self) -> None:
        ...

    