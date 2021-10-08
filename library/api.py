#coding: utf-8

import json

import redis
import datetime
import random
try:
    import psutil
except ImportError:
    psutil = None
import traceback


class Redis:


    def __init__(self, base_name='request_logs', convert_sc=None, convert_val=None):

        self.R = redis.Redis()
        self.base_name = base_name
        self.convert_sc = convert_sc or self._conv_sc
        self.convert_val = convert_val or self._conv_val
        self.delete_values()


    def _conv_sc(self, score):
        return score

    def _conv_val(self, value):
        return value


    def delete_values(self, start=None, end=None):

        start_pos = self.convert_sc(start)
        end_pos = self.convert_sc(end)
        if not start_pos and not end_pos:
            self.R.zremrangebyscore(self.base_name, '-inf', '+inf')
        if start_pos and end_pos:
            self.R.zremrangebyscore(self.base_name, start_pos, end_pos)
        if start_pos:
            self.R.zremrangebyscore(self.base_name, start_pos, '+inf')
        if end_pos:
            self.R.zremrangebyscore(self.base_name, '-inf', end_pos)

        return 'Ok'

    def get_values(self, start=None, end=None):

        ret_val = []
        start_pos = self.convert_sc(start) or 0
        end_pos = self.convert_sc(end)
        for el in self.R.zscan_iter(self.base_name):
            if el[1] >= start_pos and (not end_pos or (end_pos and el[1] <= end_pos)):
                ret_val.append({self.convert_sc(el[1]):self.convert_val(el[0].decode())})

        return ret_val


    def set_value(self, data, score):

        return self.R.zadd(self.base_name, {self.convert_val(data): self.convert_sc(score)})


class API:
    """
    test
    """

    def __init__(self):

        self.r = Redis('request_log', self._convert_sc, self._convert_val)


    def get_intervals(self, json_data):
        success = True
        start = json_data.get('start')
        if start and (start.find(':')==-1 or not start.replace(':', '').isdigit()):
            success = False
        end = json_data.get('end')
        if end and (end.find(':')==-1 or not end.replace(':', '').isdigit()):
            success = False

        return success, start, end


    def _convert_sc(self, score):

        if score is None:
            return score

        if isinstance(score, str):
            converted = int(f"1{score.replace(':', '')}")
        else:
            converted = str(int(score))[1:]
            converted = ':'.join([converted[i:i+2] for i in range(0, len(converted), 2)])
        return converted


    def _convert_val(self, value):
        return value


    def _convert(self, data):
        if isinstance(data, str):
            return json.loads(data)
        else:
            return json.dumps(data)


    def _save_data(self, method, data):

        now = datetime.datetime.now()
        score = now.strftime('%m:%d:%H:%M:%S')
        payload = self._convert({'method': method, 'data': data})
        return self.r.set_value(payload, score)


    def _get_loads(self, cpu=False, mem=False, gpu=False):

        # запрашиваем данные о системе: CPU, MEM, GPU
        # определяем тип видеокарты и делаем запрос исходя из этого
        # для nvidia: "nvidia-smi -q -d UTILIZATION"
        loads = []
        if cpu:
            cpu_load = psutil.cpu_percent() if psutil else random.random()*100
            loads.append(f"CPU: {round(cpu_load, 2)}%")
        if mem:
            mem_load = psutil.virtual_memory().percent if psutil else random.random()*100
            loads.append(f"MEM: {round(mem_load, 2)}%")
        if gpu:
            loads.append(f"GPU: {round(random.random()*100, 2)}%")

        return '; '.join(loads)


    def _parse_types(self, load_types):

        ret_types = []
        if load_types.get('cpu'):
            ret_types.append(True)
        else:
            ret_types.append(False)
        if load_types.get('mem'):
            ret_types.append(True)
        else:
            ret_types.append(False)
        if load_types.get('gpu'):
            ret_types.append(True)
        else:
            ret_types.append(False)
        return ret_types


    def get_get_load(self):
        # Получаем данные о нагрузке
        # записываем в редис время запроса, метод запроса и данные о нагрузке
        # возвращаем данные о нагрузке

        load = self._get_loads(True, True, True)
        self._save_data("GET", load)
        return load


    def get_post_load(self, load_types=None):
        # Получаем данные о нагрузке
        # записываем в редис время запроса, метод запроса и данные о нагрузке
        # возвращаем данные о нагрузке
        load_t = self._parse_types(load_types)

        load = self._get_loads(*load_t)
        self._save_data("POST", load)
        return load


    def get_history(self):
        #получаем из редиса все данные о нагрузке
        # 'MM:DD:hh:mm:ss':  'метод запроса   данные о нагрузке'

        hist = self.r.get_values()
        h_ret = []
        for i in hist:
            k, v = list(i.items())[0]
            val = self._convert(v)
            app_val = f"{val['method']}  {val['data']}"
            h_ret.append({k: app_val})
        return h_ret

    def clear(self, json_data=None):
        # Если указано 1-е значение интервала - удаляем от него и до конца
        # Если указанно второе значение интервала - удаляем от начала и до него
        # Если указаны оба значения интервала - удаляем все что между ними
        # Если интервалы не указанны - удаляем все записи

        json_data = json_data or {}
        success, start, end = self.get_intervals(json_data)
        if success:
            return self.r.delete_values(start, end)
        else:
            return 'values error'


