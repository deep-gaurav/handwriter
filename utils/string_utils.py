def accomodate_list_to_character_limit(lines):
    global formatted_lines
    formatted_lines = []

    def split_if_greater(line, character_limit=70):
        global formatted_lines
        if len(line) > character_limit:
            # print("Input Line greater than ", character_limit,
            #       " characters. Moving to a new line.")
            wheretocut = character_limit - 2
            while (line[wheretocut-1]!=' ' or line[wheretocut]!=' ') and wheretocut>1:
                wheretocut-=1
            if wheretocut <= 2:
                wheretocut = character_limit-2
            line_2 = line[wheretocut:]  # Later longs part
            line_1 = line[:wheretocut].rstrip()  # First part
            formatted_lines.append(line_1)
            split_if_greater(line_2)
        else:
            formatted_lines.append(line)
            return None

    final_list = []
    for line_l in lines:
        formatted_lines = []
        split_if_greater(line_l)
        for l in formatted_lines:
            final_list.append(l)

    return final_list


def replace_characters_absent_from_characterset(lines):
    character_set = None
    # 'Q', 'X' and 'Z
    raise NotImplementedError
