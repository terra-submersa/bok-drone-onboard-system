import logging
import random

logger = logging.getLogger(__name__)


class MockBNO08X:
    fail_rate: float = 0

    def __init__(self, fail_rate: float = 0.):
        self.fail_rate = fail_rate

    @property
    def quaternion(self):
        if random.random() < self.fail_rate:
            raise OSError("MockBNO08X: Random fail error")
        return random.random(), random.random(), random.random(), random.random()


def load_bno(is_mock: bool = False) -> ():
    if is_mock:
        return MockBNO08X(fail_rate=0.01)
    return load_bno_real()


def load_bno_real():
    import adafruit_bno08x
    import board
    import busio
    from adafruit_bno08x import (
        BNO_REPORT_ACCELEROMETER,
        BNO_REPORT_GYROSCOPE,
        BNO_REPORT_MAGNETOMETER,
        BNO_REPORT_ROTATION_VECTOR,
    )
    from adafruit_bno08x.i2c import BNO08X_I2C

    i2c = busio.I2C(board.SCL, board.SDA)  # , frequency=800000)

    logger.info("Connecting to BNO08x over I2C...")
    bno = BNO08X_I2C(i2c)

    bno.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)

    bno.enable_feature(BNO_REPORT_ACCELEROMETER)
    bno.enable_feature(BNO_REPORT_GYROSCOPE)
    bno.enable_feature(BNO_REPORT_MAGNETOMETER)
    bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    return bno
