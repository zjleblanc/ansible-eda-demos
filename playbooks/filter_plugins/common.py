class FilterModule(object):

    def filters(self):
        return { 
            "codify": self.do_codify,
            "parse_top" : self.do_parse_top,
            "num_gt": self.do_num_gt
        }

    def do_codify(self, content, endline='\n'):
        return '[code]<pre>' + content.replace(endline,'<br>').replace(' ','&nbsp;') + '</pre>[/code]'
    
    def do_num_gt(self, tasks: list, key: str, threshold: float) -> list:
        return list(filter(lambda t: float(t[key]) > threshold, tasks))
    
    def do_parse_top(self, top_raw: list) -> dict:
        parsed = {"meta": {}, "tasks": []}
        idx = 0
        for line in top_raw:
            line = line.lower().strip()
            if line.startswith("tasks"):
                parsed["meta"]["tasks"] = self.__parse_meta_line(line, int)
            elif line.startswith("%cpu"):
                parsed["meta"]["cpu"] = self.__parse_meta_line(line, float)
            elif line.startswith("mib mem"):
                parsed["meta"]["mem (mb)"] = self.__parse_meta_line(line, float)
            elif line.startswith("mib swap"):
                # special case
                line = line.replace("used.", "used,")
                parsed["meta"]["swap (mb)"] = self.__parse_meta_line(line, float)
            elif line.startswith("pid"):
                break
            idx += 1

        parsed["tasks"] = self.__parse_task_data(top_raw[idx:])
        return parsed
    
    # Private helper functions #
    @staticmethod
    def __parse_meta_line(line: str, type: type) -> dict:
        meta = {}
        stats = line.split(",")
        stats[0] = stats[0].split(":")[-1].strip()
        for stat in stats:
            stat = stat.strip()
            tokens = stat.split(" ", 1)
            if len(tokens) != 2:
                continue
            meta[tokens[1]] = type(tokens[0])
        return meta

    @staticmethod
    def __parse_task_data(lines: list) -> list:
        keys = lines[0].split()
        num_keys = len(keys)
        parsed = []
        for line in lines[1:]:
            data = {}
            values = line.split()
            for idx in range(0, num_keys):
                data[keys[idx]] = values[idx]
            parsed.append(data)
        return parsed