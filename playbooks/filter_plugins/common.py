class FilterModule(object):

    def filters(self):
        return { 
            "codify": self.do_codify,
            "parse_top" : self.do_parse_top,
            "parse_lsof" : self.do_parse_lsof,
            "num_gt": self.do_num_gt
        }

    def do_codify(self, content, endline='\n'):
        return '[code]<pre>' + content.replace(endline,'<br>') + '</pre>[/code]'
    
    def do_num_gt(self, tasks: list, key: str, threshold: float) -> list:
        return list(filter(lambda t: float(t[key]) > threshold, tasks))
    
    def do_parse_lsof(self, lsof_raw: list) -> list:
        return self.__parse_lsof_records(lsof_raw)    
    
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
        print(num_keys)
        parsed = []
        for line in lines[1:]:
            data = {}
            values = line.split()
            for idx in range(0, num_keys):
                data[keys[idx]] = values[idx]
            parsed.append(data)
        return parsed
    
    @staticmethod
    def __parse_lsof_records(lines: list) -> dict:
        parsed = {}
        pid = 'ERR'
        for line in lines:
            if line[0] == 'p':
                pid = line[1:]
                parsed[pid] = {"pid": pid}
                continue
            if line[0] == 'f':
                parsed[pid]['file_descriptor'] = line[1:]
                continue
            if line[0] == 'a':
                parsed[pid]['access_mode'] = line[1:]
                continue
            if line[0] == 'c':
                parsed[pid]['command_name'] = line[1:]
                continue
            if line[0] == 'C':
                parsed[pid]['file_struct_share_count'] = line[1:]
                continue
            if line[0] == 'd':
                parsed[pid]['file_device_character_code'] = line[1:]
                continue
            if line[0] == 'D':
                parsed[pid]['file_device_num'] = line[1:]
                continue
            if line[0] == 'F':
                parsed[pid]['file_struct_addr'] = line[1:]
                continue
            if line[0] == 'G':
                parsed[pid]['file_flags'] = line[1:]
                continue
            if line[0] == 'i':
                parsed[pid]['file_inode_num'] = line[1:]
                continue
            if line[0] == 'k':
                parsed[pid]['file_link_count'] = line[1:]
                continue
            if line[0] == 'l':
                parsed[pid]['file_lock_status'] = line[1:]
                continue
            if line[0] == 'L':
                parsed[pid]['proc_login_name'] = line[1:]
                continue
            if line[0] == 'n':
                parsed[pid]['file_name_comment_addr'] = line[1:]
                continue
            if line[0] == 'N':
                parsed[pid]['node_identifier'] = line[1:]
                continue
            if line[0] == 'o':
                parsed[pid]['file_offset'] = line[1:]
                continue
            if line[0] == 'g':
                parsed[pid]['proc_group_id'] = line[1:]
                continue
            if line[0] == 'P':
                parsed[pid]['protocol_name'] = line[1:]
                continue
            if line[0] == 'r':
                parsed[pid]['raw_device_number'] = line[1:]
                continue
            if line[0] == 'R':
                parsed[pid]['proc_parent_pid'] = line[1:]
                continue
            if line[0] == 's':
                parsed[pid]['file_size'] = line[1:]
                continue
            if line[0] == 'S':
                parsed[pid]['file_stream_id'] = line[1:]
                continue
            if line[0] == 't':
                parsed[pid]['file_type'] = line[1:]
                continue
            if line[0] == 'u':
                parsed[pid]['proc_user_id'] = line[1:]
                continue
            if line[0] == 'Z':
                parsed[pid]['selinux_context'] = line[1:]
                continue
        return parsed