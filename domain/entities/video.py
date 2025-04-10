from dataclasses import dataclass


@dataclass
class Video:
    def __init__(self, file_name, file_size, content, user_email):
        self.file_name = file_name
        self.file_size = file_size
        self.content = content
        self.user_email = user_email

    def __str__(self):
        return f"Video(file_name={self.file_name}, file_size={self.file_size}, content={self.content}, user_email={self.user_email})"
