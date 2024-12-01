externalTemperature = 20  # TODO Wrap loose parameters into model
groundTemperature = 10


class Signal:
    def __init__(self):
        self._subscribers = []

    def connect(self, callback):
        self._subscribers.append(callback)

    def emit(self, *args, **kwargs):
        for subscriber in self._subscribers:
            subscriber(*args, **kwargs)


class Room:  # TODO Migrate from pure Python files to SQLAlchemy
    def __init__(self, length, width, height):
        self.length = length
        self.width = width
        self.height = height
        self.temperature = None
        self.heat_loss = 0
        self.walls = []

        for i in range(6):
            wall = Wall()
            wall.set_index(i)  # TODO Hard code indices
            wall.changed.connect(self.on_wall_changed)
            self.walls.append(wall)

        self.walls[0].set_area(self.width, self.length)
        self.walls[1].set_area(self.width, self.height)
        self.walls[2].set_area(self.width, self.height)
        self.walls[3].set_area(self.length, self.height)
        self.walls[4].set_area(self.length, self.height)
        self.walls[5].set_area(self.width, self.length)

    @classmethod
    def from_dict(cls, data):
        room = cls(data['length'], data['width'], data['height'])
        walls = [Wall.from_dict(wall) for wall in data['walls']]
        room.length = data['length']  #
        room.width = data['width']
        room.height = data['height']  # REDUNDANT since defined in cls, TODO needs attention to make consistent with other classes such as Wall
        room.temperature = data['temperature']
        room.heat_loss = data['heat_loss']
        room.walls = walls
        return room

    @staticmethod
    def get_exclude_list():
        return ['walls']

    def on_wall_changed(self, wall):
        wall.calculate_heat_loss(self)

    def set_length(self, length):  # TODO implement Observer event-driven signals to trigger re-calculations
        self.length = length
        self.walls[0].set_area(self.width, self.length)
        self.walls[3].set_area(self.length, self.height)
        self.walls[4].set_area(self.length, self.height)
        self.walls[5].set_area(self.width, self.length)
        self.calculate_room_heat_loss()

    def set_height(self, height):
        self.height = height
        self.walls[1].set_area(self.width, self.height)
        self.walls[2].set_area(self.width, self.height)
        self.walls[3].set_area(self.length, self.height)
        self.walls[4].set_area(self.length, self.height)
        self.calculate_room_heat_loss()

    def set_width(self, width):
        self.width = width
        self.walls[0].set_area(self.width, self.length)
        self.walls[1].set_area(self.width, self.height)
        self.walls[2].set_area(self.width, self.height)
        self.walls[5].set_area(self.width, self.length)
        self.calculate_room_heat_loss()

    def set_room_temperature(self, temperature):
        self.temperature = temperature

    def set_wall_uvalues(self, values):
        for i in range(6):
            self.walls[i].set_uvalue(values[i], room=self)
        self.calculate_room_heat_loss()

    def set_wall_uvalue(self, index, value):
        self.walls[index].set_uvalue(value, room=self)
        self.calculate_room_heat_loss()

    def calculate_wall_heat_losses(self):
        for i in range(6):
            self.calculate_wall_heat_loss(i)

    def calculate_wall_heat_loss(self, index):
        self.walls[index].calculate_heat_loss(self)

    def calculate_room_heat_loss(self):
        self.heat_loss = 0
        for wall in self.walls:
            self.heat_loss += wall.Q


class Wall:
    def __init__(self):  # TODO Change property table viewing system; soon the class may contain lots of additional properties that aren't made for viewing. Perhaps put viewable properties in a list or subclass?
        self.index = None
        self.Area = None
        self.UValue = None
        self.Q = None
        self.changed = Signal()  # Currently in exclude_list

    @classmethod
    def from_dict(cls, data):
        wall = cls()
        wall.index = data['index']
        wall.Area = data['Area']
        wall.UValue = data['UValue']
        wall.Q = data['Q']
        return wall

    @staticmethod
    def get_exclude_list():
        return ['changed']  # TODO

    def set_index(self, index):
        self.index = index

    def set_area(self, x, y,):
        self.Area = x * y
        self.changed.emit(self)

    def set_uvalue(self, value, room=None):
        self.UValue = value
        if room is not None:
            self.calculate_heat_loss(room)

    def calculate_heat_loss(self, room):
        if self.Area is not None and self.UValue is not None:
            sink_temperature = self.get_sink_temperature()
            self.Q = self.Area * self.UValue * (room.temperature - sink_temperature)

    def get_sink_temperature(self):
        if self.index == 0:
            return groundTemperature
        else:
            return externalTemperature
