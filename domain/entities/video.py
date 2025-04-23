from dataclasses import dataclass


@dataclass
class Video:
    def __init__(self, file_name, file_size, content, user_email,user_id, path_s3):
        self.file_name = file_name
        self.file_size = file_size
        self.content = content
        self.user_email = user_email
        self.user_id = user_id
        self_path_s3 = path_s3

    def __str__(self):
        return f"Video(file_name={self.file_name}, file_size={self.file_size}, content={self.content}, user_email={self.user_email}, user_id={self.user_id}, path_s3={self.path_s3})"
