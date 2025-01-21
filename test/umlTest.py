class Engine:
    def __init__(self, engine_type, horsepower):
        self.engine_type = engine_type
        self.horsepower = horsepower

    def get_engine_info(self):
        return f"Engine Type: {self.engine_type}, Horsepower: {self.horsepower}"


class Car:
    def __init__(self, make, model, engine: Engine):
        self.make = make
        self.model = model
        self.engine = engine  # 确保 Car 类持有 Engine 类的实例

    def get_car_info(self):
        return f"Car Make: {self.make}, Model: {self.model}, Engine: {self.engine.get_engine_info()}"



# 创建 Engine 和 Car 的实例
engine = Engine("V8", 450)
car = Car("Tesla", "Model S", engine)

# 打印汽车信息
print(car.get_car_info())