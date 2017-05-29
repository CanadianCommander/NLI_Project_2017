from copy import copy


class ArgumentType:
    INVALID_ARGUMENT    = 0
    EXTRACT_PHONEME     = 1
    RAW_STRING          = 2


class Argument:

    def __init__(self, str_arg="", type_id=ArgumentType.INVALID_ARGUMENT, arr_sub_args=[]):
        self.string = str_arg
        self.type_id = type_id
        self.sub_args = arr_sub_args

        # if the user does not pass a list
        # convert to one
        if type(self.sub_args) is not list:
            self.sub_args = [self.sub_args]

    def get_type(self):
        return self.type_id

    def get_string(self):
        return self.string

    def get_sub_args(self):
        return copy(self.sub_args)

    def iter_sub_args(self):
        for x in self.sub_args:
            yield x

    def __iter__(self):
        for s_arg in self.sub_args:
            yield s_arg

    def __eq__(self, other):
        if self.string == other.string and self.type_id == other.type_id:
            return True
        return False