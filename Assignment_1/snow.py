import time
import threading
from flask import Flask, request, jsonify

class SnowflakeIDGenerator:
    def __init__(self, machine_id):
        self.machine_id = machine_id  # 机器标识符
        self.sequence = 0  # 序列号
        self.last_timestamp = -1  # 上一次生成ID的时间戳
        self.lock = threading.Lock()  # 线程锁，确保线程安全

        # 定义位数
        self.timestamp_bits = 32
        self.machine_id_bits = 5
        self.sequence_bits = 5

        # 定义最大值
        self.max_machine_id = (1 << self.machine_id_bits) - 1
        self.max_sequence = (1 << self.sequence_bits) - 1

        # 定义位移
        self.timestamp_shift = self.machine_id_bits + self.sequence_bits
        self.machine_id_shift = self.sequence_bits

        # 检查机器标识符是否合法
        if self.machine_id > self.max_machine_id or self.machine_id < 0:
            raise ValueError(f"Machine ID must be between 0 and {self.max_machine_id}")

    def _current_timestamp(self):
        """获取当前时间戳（秒）"""
        return int(time.time())

    def _wait_for_next_timestamp(self, last_timestamp):
        """等待到下一秒"""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        """生成唯一 ID"""
        with self.lock:
            timestamp = self._current_timestamp()

            # 如果当前时间戳小于上一次生成ID的时间戳，说明系统时钟回拨
            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID.")

            # 如果当前时间戳等于上一次生成ID的时间戳，则递增序列号
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                # 如果序列号溢出，则等待到下一秒
                if self.sequence == 0:
                    timestamp = self._wait_for_next_timestamp(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # 生成 ID
            id = (
                (timestamp << self.timestamp_shift) |
                (self.machine_id << self.machine_id_shift) |
                self.sequence
            )
            return id
        

app = Flask(__name__)
url_mapping = {}

# 初始化 Snowflake ID 生成器
id_generator = SnowflakeIDGenerator(machine_id=1)  # 假设当前机器标识符为 1

@app.route('/', methods=['POST'])
def create_short_url():
    data = request.get_json()
    url = data.get('value')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    # 生成唯一 ID
    short_id = id_generator.generate_id()
    url_mapping[short_id] = url

    return jsonify({"id": short_id}), 201

@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id in url_mapping:
        return jsonify({"value": url_mapping[short_id]}), 301
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(port=5000)