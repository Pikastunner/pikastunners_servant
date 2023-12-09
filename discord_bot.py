import discord
from datetime import datetime
import random
import regex as re
from tabulate import tabulate
import pandas as pd
from io import BytesIO
import sys
import json
import pprint
import sys
import streamlit as st
import os

# 0 is Pikastunner
# 1 is Gekokillol
token = os.environ['token'] = st.secrets['token']


bot_data = [#{"channel_id": 1124323950235754537, 
            #"guild_id": 1110051126071533649, 
            #"token": "MTEyNDMxMTUwODkyNzY2NDE0OQ.GQkAcz._ZEnifs8vbzy1jbLA_chlX-7eshPMLe-TgrUyA"}, 
            {"channel_id": 1145338676470100118, 
            "guild_id": 1106222465618825328, 
            "token": token}]


#if len(sys.argv) != 2:
#    sys.exit("Need the server argument")
#elif not sys.argv[1].isnumeric():
#    sys.exit("Argument must be an integer")
#elif int(sys.argv[1]) > len(bot_data) - 1:
#    sys.exit(f"Argument must be a valid integer that is less than {sys.argv[1]}")

server_index = 0

channel_id = bot_data[server_index]["channel_id"]
guild_id = bot_data[server_index]["guild_id"]
token =  bot_data[server_index]["token"]

intents = discord.Intents.default()
#intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)


# Timetable Classes
class Course:
    def __init__(self, labs, tuts, uocs) -> None:
        self.lab_days = labs
        self.tut_days = tuts
        self.uocs = uocs
    def update_info(self, param, change):
        if param == "lab_days":
            self.lab_days = change
        elif param == "tut_days":
            self.tut_days == change
        else:
            self.uocs = int(change)

class Term:
    def __init__(self, courses, completed) -> None:
        courses_obj = {}
        for course in courses:
            labs = courses[course]["lab_days"]
            tuts = courses[course]["tut_days"]
            uocs = courses[course]["uocs"]
            course_obj = Course(labs, tuts, uocs)
            courses_obj.update({course: course_obj})
        self.courses = courses_obj
        self.completed = completed
    def update_course(self, course_name, lab_days, tut_days, uocs):
        self.courses[course_name] = Course(lab_days, tut_days, uocs)
    def update_completion(self, completion):
        self.completed = completion
    def remove_course(self, course_name):
        del self.courses[course_name]
    def courses_dict(self):
        courses_dict = {
            course: {
                "lab_days": self.courses[course].lab_days,
                "tut_days": self.courses[course].tut_days,
                "uocs": self.courses[course].uocs
            }
            for course in self.courses
        }
        return courses_dict

class Year:
    def __init__(self, year, t1, t2, t3) -> None:
        self.year_name = year
        self.term_1 = Term(t1[0], t1[1])
        self.term_2 = Term(t2[0], t2[1])
        self.term_3 = Term(t3[0], t3[1])
    def update_term(self, term, courses, completed):
        if term == "t1":
            self.term_1 = Term(courses, completed)
        elif term == "t2":
            self.term_2 = Term(courses, completed)
        else:
            self.term_3 = Term(courses, completed)

class Timetable:
    def __init__(self, years) -> None:
        years_obj = {}
        for year in years:
            terms = {"t1": None, "t2": None, "t3": None}
            for term in terms.keys():
                courses = years[year][term]["courses"]
                completed = years[year][term]["completed"]
                terms[term] = [courses, completed]#Term(courses, completed)
            year_obj = Year(year, terms["t1"], terms["t2"], terms["t3"])
            years_obj.update({year: year_obj})
        self.years = years_obj
    def update_year(self, new_year, t1, t2, t3):
        self.years[new_year] = Year(new_year, t1, t2, t3)
    def to_dict(self):
        years_dict = {
            year: {
                't1': {
                    "courses": self.years[year].term_1.courses_dict(),
                    "completed": self.years[year].term_1.completed
                },
                't2':  {
                    "courses": self.years[year].term_2.courses_dict(),
                    "completed": self.years[year].term_2.completed
                },
                't3': {
                    "courses": self.years[year].term_3.courses_dict(),
                    "completed": self.years[year].term_3.completed
                }
            }
            for year in self.years
        }
        return years_dict

class User:
    def __init__(self, name, uocs_completed, total_uocs, timetable) -> None:
        self.name = name
        self.uocs_completed = uocs_completed
        self.total_uocs = total_uocs
        self.timetable = timetable
    def to_dict(self):
        user_dict = {
            self.name : {
                'uocs_completed': self.uocs_completed,
                'total_uocs': self.total_uocs,
                'timetable': {
                    'year': self.timetable
                }
            }
        }
        return user_dict
    def update_uocs_completed(self, completed_uocs):
        self.uocs_completed += completed_uocs

# Timetable Command Classes
class AddUser:
    def __init__(self, args) -> None:
        if len(args) != 4:
            self.command = None
        else:
            self.command = args[0]
            self.name = args[1]
            self.uocs_completed = int(args[2])
            self.total_uocs = int(args[3])
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /add_user command.")
            raise ValueError("Incorrect number of arguments for /add_user command.")
        #elif self.total_uocs < self.uocs_completed:
         #   await channel.send("Total UoCs must be lower than or equal to UoCs completed.")
          #  raise ValueError("Total UoCs must be lower than or equal to UoCs completed.")
        elif self.name in existing_data["Users"].keys():
            await channel.send(f"User named {self.name} already exists.")
            raise ValueError(f"User named {self.name} already exists.")
        else:
            new_user = User(self.name, self.uocs_completed, self.total_uocs, {})
            user_dict = new_user.to_dict()
            pprint.pprint(existing_data)
            existing_data["Users"].update(user_dict)
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Added {self.name}.")

class SelectUser:
    def __init__(self, args) -> None:
        if len(args) != 2:
            self.command = None
        else:
            self.command = args[0]
            self.selected = args[1]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /select_user command.")
            raise ValueError("Incorrect number of arguments for /select_user command.")
        elif self.selected not in existing_data["Users"].keys():
            await channel.send(f"User named {self.selected} does not exists.")
            raise ValueError(f"User named {self.selected} does not exists.")
        elif self.selected == existing_data["Selected_user"]:
            await channel.send(f"Already selected user named {self.selected}.")
            raise ValueError(f"Already selected user named {self.selected}.")
        else:
            existing_data["Selected_user"] = self.selected
            existing_data["Selected_timetable"] = ""
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Selected {self.selected}.")

class AddTimetable:
    def __init__(self, args) -> None:
        if len(args) != 2:
            self.command = None
        else:
            self.command = args[0]
            self.year = args[1]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /add_timetable command.")
            raise ValueError("Incorrect number of arguments for /add_timetable command.")
        elif not self.year.isdigit():
            await channel.send("Year must be an integer.")
            raise ValueError("Year must be an integer.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            timetable_obj.update_year(self.year, [{}, False], [{}, False], [{}, False])
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            pprint.pprint(existing_data)
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Added timetable for year {self.year}.")

class SelectTimetable:
    def __init__(self, args) -> None:
        if len(args) != 3:
            self.command = None
        else:
            self.command = args[0]
            self.view_year = args[1]
            self.view_term = args[2]
    async def execute(self, channel, args, existing_data):
        selected_user = existing_data["Selected_user"]
        if self.command == None:
            await channel.send("Incorrect number of arguments for /select_timetable command.")
            raise ValueError("Incorrect number of arguments for /select_timetable command.")
        elif not self.view_year.isdigit():
            await channel.send("Year must be an integer.")
            raise ValueError("Year must be an integer.")
        elif self.view_term not in ["t1", "t2", "t3"]:
            await channel.send("Must be a valid term.")
            raise ValueError("Must be a valid term.")
        elif self.view_year not in existing_data["Users"][selected_user]["timetable"]["year"].keys():
            await channel.send(f"Year {self.selected} does not exists.")
            raise ValueError(f"Year {self.selected} does not exists.")
        elif [self.view_year, self.view_term] == existing_data["Selected_timetable"]:
            await channel.send(f"Already selected year {self.view_year}, term {self.view_term}.")
            raise ValueError(f"Already selected year {self.view_year}, term {self.view_term}.")
        else:
            existing_data["Selected_timetable"] = [self.view_year, self.view_term]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Selected year {self.view_year}, term {self.view_term}.")

class AddCourse:
    def __init__(self, args) -> None:
        if len(args) != 5:
            self.command = None
        elif not args[4].isnumeric():
            self.uocs = None
        else:
            self.command = args[0]
            self.course_name = args[1][:4].upper() + args[1][4:]
            self.lab_days = args[2]
            self.tut_days = args[3]
            self.uocs = int(args[4])
    async def execute(self, channel, args, existing_data):
        def check_format(self):
            lab_days = [date.strip() for date in self.lab_days.split(",")]
            tut_days = [date.strip() for date in self.tut_days.split(",")]
            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            for day_time in lab_days + tut_days:
                day = day_time.split(" ")[0]
                if day not in all_days:
                    return f"{day} is not a valid day"
                time = day_time.split(" ")[1].split("-")
                if len(time) == 1:
                    return f"Incorrect time format at {day_time} involving hyphen."
                validate_time = lambda time: datetime.strptime(time, "%H:%M").time() if len(time.split(':')) == 2 and all(part.isdigit() for part in time.split(':')) else None
                start_time = validate_time(time[0])
                end_time = validate_time(time[1])
                if start_time == None:
                    return f"Incorrect time format at {time[0]}."
                elif end_time == None:
                    return f"Incorrect time format at {time[1]}."
                if start_time > end_time:
                    return f"Start time cannot be later than end time."
            return ""
        def check_exceed(self, existing_data, selected_user, selected_timetable):
            curr_uocs = sum([course_info["uocs"] for course_info in existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"].values()])
            if curr_uocs + self.uocs > 18:
                return True
            else:
                return False
        if self.command == None:
            await channel.send("Incorrect number of arguments for /add_course command.")
            raise ValueError("Incorrect number of arguments for /add_course command.")
        elif self.uocs == None:
            await channel.send("UoCs must be an integer.")
            raise ValueError("UoCs must be an integer.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        elif len(days_format := check_format(self)) > 0:
            await channel.send(days_format)
            raise ValueError(days_format)
        elif check_exceed(self, existing_data, selected_user, selected_timetable):
            await channel.send("Cannot add more than 18 UoCs.")
            raise ValueError("Cannot add more than 18 UoCs.")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            if selected_timetable[1] == "t1":
                timetable_obj.years[selected_timetable[0]].term_1.update_course(self.course_name, self.lab_days, self.tut_days, self.uocs)
            elif selected_timetable[1] == "t2":
                timetable_obj.years[selected_timetable[0]].term_2.update_course(self.course_name, self.lab_days, self.tut_days, self.uocs)
            else:
                timetable_obj.years[selected_timetable[0]].term_3.update_course(self.course_name, self.lab_days, self.tut_days, self.uocs)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Added course named {self.course_name} in year {selected_timetable[0]}, term {selected_timetable[1]}.")
        
class CompleteTerm:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /complete_term command.")
            raise ValueError("Incorrect number of arguments for /complete_term command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        elif existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["completed"] == True:
            await channel.send("Term has already been completed.")
            raise ValueError("Term has already been completed.")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            if selected_timetable[1] == "t1":
                timetable_obj.years[selected_timetable[0]].term_1.update_completion(True)
            elif selected_timetable[1] == "t2":
                timetable_obj.years[selected_timetable[0]].term_2.update_completion(True)
            else:
                timetable_obj.years[selected_timetable[0]].term_3.update_completion(True)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            courses_dict = existing_years[selected_timetable[0]][selected_timetable[1]]["courses"]
            courses_count = sum([courses_dict[course]["uocs"] for course in courses_dict])
            modify_user.update_uocs_completed(courses_count)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Completed term {selected_timetable[1]} in year {selected_timetable[0]}.")
            if uocs_complete + courses_count > total_uocs:
                await channel.send(f"Congratulations you have finished all the required UoCs.")

class CheckProgression:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        def strikethrough_text(text):
            return '\u0336' + '\u0336'.join(text)
        def extract_courses(term, existing_years, year):
            term_info = existing_years[year][term]
            if term_info["completed"] == True:
                courses_string = "\n".join([strikethrough_text(course) for course in term_info["courses"].keys()])
            else:
                courses_string = "\n".join(term_info["courses"].keys())
            return courses_string
        if self.command == None:
            await channel.send("Incorrect number of arguments for /check_progression command.")
            raise ValueError("Incorrect number of arguments for /check_progression command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        else:
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            await channel.send(f"The progress of {selected_user} is the following\n")
            uocs_completed = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            if uocs_completed >= total_uocs:
                await channel.send(f"- {selected_user} has completed {uocs_completed} UoCs which is enough credits to complete their degree of {total_uocs} UoCs")
            else:
                uoc_diff = total_uocs - uocs_completed
                await channel.send(f"- {selected_user} has completed {uocs_completed} UoCs requiring {uoc_diff} more uOcs to complete their degree of {total_uocs} UoCs")
            if len(existing_years) > 0:
                progression_df = pd.DataFrame()
                terms_list = ["t1", "t2", "t3"]
                terms = {"t1": None, "t2": None, "t3": None}
                progression_df.index = terms_list
                for year in existing_years:
                    for term in terms_list:
                        courses = extract_courses(term, existing_years, year)
                        terms.update({term: courses})
                    progression_df[year] = terms.values()
                progression_df = progression_df.sort_index(axis=1)
                table = tabulate(progression_df, headers='keys', tablefmt='grid')
                text_bytes = table.encode('utf-8')
                text_io = BytesIO(text_bytes)
                await channel.send(file=discord.File(text_io, filename="message.txt"))
            else:
                await channel.send(f"- {selected_user} has no logged years.")
                
class VisualiseTimetable:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /visualise_timetable command.")
            raise ValueError("Incorrect number of arguments for /visualise_timetable command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        else:
            timetable_df = pd.DataFrame()
            days = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": []}
            courses = existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"]
            for course in courses:
                labs = [{times.strip().split(" ")[0]: [f"Lec ({course})", times.strip().split(" ")[1]]} for times in courses[course]["lab_days"].split(",")]
                tuts = [{times.strip().split(" ")[0]: [f"Tut ({course})", times.strip().split(" ")[1]]} for times in courses[course]["tut_days"].split(",")]
                for info in labs + tuts:
                    for key, value in info.items():
                        days[key].append(value)
            for day in days:
                hours = {i: "" for i in range(24)}
                for times in days[day]:
                    start = int((times[1].split("-")[0]).split(":")[0])
                    end = int((times[1].split("-")[1]).split(":")[0])
                    print(times[1].split("-")[1])
                    for i in range(start, end + 1):
                        hours[i] += " ".join(times) + "\n"
                timetable_df[day] = hours.values()
            #timetable_df.index = [f"{i}:00" for i in range(24)]
            #timetable_df.index = ["12:00am" if i == 0 else f"{i}:00am" for i in range(12)] + ["12:00pm" if i == 12 else f"{i%12}:00pm" for i in range(12, 24)]
            hours = []
            for hour in range(24):
                # Formatting the hour with leading zeros and AM/PM
                formatted_hour = "{:02d}:00{}".format(hour if hour < 12 else hour - 12, "am" if hour < 12 else "pm")
                if formatted_hour[:2] == "00":
                    formatted_hour = "12" + formatted_hour[2:]
                hours.append(formatted_hour)
            timetable_df.index = hours
            table = tabulate(timetable_df, headers='keys', tablefmt='grid')
            text_bytes = table.encode('utf-8')
            text_io = BytesIO(text_bytes)
            await channel.send(f"{selected_user}'s timetable for {selected_timetable[0]}{selected_timetable[1]}\n")
            await channel.send(file=discord.File(text_io, filename="message.txt"))

class ModifyUser:
    def __init__(self, args) -> None:
        if len(args) != 3:
            self.command = None
        else:
            if not all([digit.isnumeric() for digit in args[2].split("/")]):
                self.command = args[0]
                self.to_modify = None
            else:
                self.command = args[0]
                self.to_modify = args[1]
                self.modify_values = args[2]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /modify_user command.")
            raise ValueError("Incorrect number of arguments for /modify_user command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif self.to_modify == None:
            await channel.send("All UoC related modifications must be integer changes")
            raise ValueError("All UoC related modifications must be integer changes")
        elif not all(list(parameter in ["uocs_completed", "total_uocs"] for parameter in self.to_modify.split("/"))):
            await channel.send("Unknown parameter being changed")
            raise ValueError("Unknown parameter being changed")
        elif len(modify_params := self.to_modify.split("/")) != len(change_params := self.modify_values.split("/")):
            await channel.send("Number of parameters to be changed must be equal to the given changes")
            raise ValueError("Number of parameters to be changed must be equal to the given changes")
        else:
            print(modify_params, change_params)
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            for param, change in zip(modify_params, change_params):
                if param == "uocs_completed":
                    uocs_complete = int(change)
                else:
                    total_uocs = int(change)
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Updated {' '.join(modify_params)} for {selected_user}.")
                
class DropUser:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /drop_user command.")
            raise ValueError("Incorrect number of arguments for /drop_user command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        else:
            del existing_data["Users"][selected_user]
            existing_data["Selected_user"] = ""
            existing_data["Selected_timetable"] = []
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Deleted {selected_user}.")

class DropYear:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /drop_year command.")
            raise ValueError("Incorrect number of arguments for /drop_year command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        else:
            del existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]]
            existing_data["Selected_timetable"] = []
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Deleted year {selected_timetable[0]} for user {selected_user}.")

class DropTimetable:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /drop_timetable command.")
            raise ValueError("Incorrect number of arguments for /drop_timetable command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            timetable_obj.years[selected_timetable[0]].update_term(selected_timetable[1], {}, False)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            pprint.pprint(existing_data)
            existing_data["Selected_timetable"] = []
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Dropped timetable in {selected_timetable[0]}{selected_timetable[1]} for user {selected_user}.")

class ModifyCourse:
    def __init__(self, args) -> None:
        if len(args) != 4:
            self.command = None
        else:
            self.command = args[0]
            self.course = args[1]
            self.to_modify = args[2]
            self.modify_values = args[3]
    async def execute(self, channel, args, existing_data):
        def check_format(modify_params, change_params):
            if "lab_days" in modify_params:
                lab_days_index = modify_params.index("lab_days")
                lab_days = change_params[lab_days_index]
            else:
                lab_days = []
            if "tut_days" in modify_params:
                tut_days_index = modify_params.index("tut_days")
                tut_days = change_params[tut_days_index]
            else:
                tut_days = []
            lab_days = [date.strip() for date in lab_days.split(",")]
            tut_days = [date.strip() for date in tut_days.split(",")]
            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            for day_time in lab_days + tut_days:
                day = day_time.split(" ")[0]
                if day not in all_days:
                    return f"{day} is not a valid day"
                time = day_time.split(" ")[1].split("-")
                if len(time) == 1:
                    return f"Incorrect time format at {day_time} involving hyphen."
                validate_time = lambda time: datetime.strptime(time, "%H:%M").time() if len(time.split(':')) == 2 and all(part.isdigit() for part in time.split(':')) else None
                start_time = validate_time(time[0])
                end_time = validate_time(time[1])
                print(start_time, end_time)
                if start_time == None:
                    return f"Incorrect time format at {time[0]}."
                elif end_time == None:
                    return f"Incorrect time format at {time[1]}."
                if start_time > end_time:
                    return f"Start time cannot be later than end time."
            return ""
        def check_uoc_format(self, modify_params, change_params, existing_data, selected_user, selected_timetable):
            def check_exceed(self, existing_data, selected_user, selected_timetable, uocs):
                curr_uocs = sum([course_info["uocs"] for course_info in existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"].values()])
                old_uocs = existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"][self.course]["uocs"]
                if curr_uocs + uocs - old_uocs > 18:
                    return True
                else:
                    return False
            if "uocs" in modify_params:
                uocs_index = modify_params.index("uocs")
                uocs = change_params[uocs_index]
                if not uocs.isdigit():
                    return "UoCs must be an integer."
                elif check_exceed(self, existing_data, selected_user, selected_timetable, int(uocs)):
                    return "Cannot add more than 18 UoCs."
                else:
                    return ""
            else:
                return "" 
        if self.command == None:
            await channel.send("Incorrect number of arguments for /modify_course command.")
            raise ValueError("Incorrect number of arguments for /modify_course command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        elif not all(parameter in ["lab_days", "tut_days", "uocs"] for parameter in self.to_modify.split("/")):
            await channel.send("Cannot change unknown parameter.")
            raise ValueError("Cannot change unknown parameter.")
        elif len(modify_params := self.to_modify.split("/")) != len(change_params := self.modify_values.split("/")):
            await channel.send("Number of parameters to be changed must be equal to the given changes.")
            raise ValueError("Number of parameters to be changed must be equal to the given changes.")
        elif self.course not in existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"].keys():
            await channel.send(f"Course named {self.course} does not exist in {selected_timetable[0]}{selected_timetable[1]}")
            raise ValueError(f"Course named {self.course} does not exist in {selected_timetable[0]}{selected_timetable[1]}")
        elif len(uoc_error_msg := check_uoc_format(self, modify_params, change_params, existing_data, selected_user, selected_timetable)) > 0:
            await channel.send(uoc_error_msg)
            raise ValueError(uoc_error_msg)
        elif len(days_format := check_format(modify_params, change_params)) > 0:
            await channel.send(days_format)
            raise ValueError(days_format)
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            for param, change in zip(modify_params, change_params):
                if selected_timetable[1] == "t1":
                    timetable_obj.years[selected_timetable[0]].term_1.courses[self.course].update_info(param, change)
                elif selected_timetable[1] == "t2":
                    timetable_obj.years[selected_timetable[0]].term_2.courses[self.course].update_info(param, change)
                else:
                    timetable_obj.years[selected_timetable[0]].term_3.courses[self.course].update_info(param, change)
                #[selected_timetable[1]].update_info(self, param, change)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Updated {' '.join(modify_params)} on course {self.course} for {selected_user}.")
 
class ModifyCompletion:
    def __init__(self, args) -> None:
        if len(args) != 1:
            self.command = None
        else:
            self.command = args[0]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /modify_completion command.")
            raise ValueError("Incorrect number of arguments for /modify_completion command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            term_status = existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["completed"]
            timetable_obj = Timetable(existing_years)
            if selected_timetable[1] == "t1":
                timetable_obj.years[selected_timetable[0]].term_1.update_completion(not term_status)
            elif selected_timetable[1] == "t2":
                timetable_obj.years[selected_timetable[0]].term_2.update_completion(not term_status)
            else:
                timetable_obj.years[selected_timetable[0]].term_3.update_completion(not term_status)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            pprint.pprint(existing_data)
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            if not term_status == True:
                string_status = "complete"
            else:
                string_status = "incomplete"
            await channel.send(f"{selected_timetable[0]}{selected_timetable[1]} is now {string_status}.")

class DropCourse:
    def __init__(self, args) -> None:
        if len(args) != 2:
            self.command = None
        else:
            self.command = args[0]
            self.course = args[1]
    async def execute(self, channel, args, existing_data):
        if self.command == None:
            await channel.send("Incorrect number of arguments for /drop_course command.")
            raise ValueError("Incorrect number of arguments for /drop_course command.")
        elif (selected_user := existing_data["Selected_user"]) == "":
            await channel.send("You must select a user before using this command.")
            raise ValueError("You must select a user before using this command.")
        elif (selected_timetable := existing_data["Selected_timetable"]) == "":
            await channel.send("You must select a timetable before using this command.")
            raise ValueError("You must select a timetable before using this command.")
        elif self.course not in existing_data["Users"][selected_user]["timetable"]["year"][selected_timetable[0]][selected_timetable[1]]["courses"].keys():
            await channel.send(f"Course named {self.course} does not exist in {selected_timetable[0]}{selected_timetable[1]}")
            raise ValueError(f"Course named {self.course} does not exist in {selected_timetable[0]}{selected_timetable[1]}")
        else:
            uocs_complete = existing_data["Users"][selected_user]["uocs_completed"]
            total_uocs = existing_data["Users"][selected_user]["total_uocs"]
            existing_years = existing_data["Users"][selected_user]["timetable"]["year"]
            timetable_obj = Timetable(existing_years)
            if selected_timetable[1] == "t1":
                timetable_obj.years[selected_timetable[0]].term_1.remove_course(self.course)
            elif selected_timetable[1] == "t2":
                timetable_obj.years[selected_timetable[0]].term_2.remove_course(self.course)
            else:
                timetable_obj.years[selected_timetable[0]].term_3.remove_course(self.course)
            new_timetable = timetable_obj.to_dict()
            modify_user = User(selected_user, uocs_complete, total_uocs, new_timetable)
            existing_data["Users"][selected_user] = modify_user.to_dict()[selected_user]
            with open("users.json", "w") as users_json:
                json.dump(existing_data, users_json, indent=4)
            await channel.send(f"Dropped {self.course} on {selected_timetable[0]}{selected_timetable[1]} for {selected_user}.")

# Restaurant Command Classes
class AddRestaurants:
    def __init__(self, args):
        if len(args) != 2:
            self.command = args[0]
            self.restaurant_name = None
        else:   
            self.command = args[0]
            self.restaurant_name = args[1]
    @bot.event
    async def execute(self, channel, args, df, line_count):
        if len(args) != 2:
            await channel.send("Incorrect number of arguments for /add_restaurants command")
            raise ValueError("Incorrect number of arguments for /add_restaurants command")
        else:
            current_time = datetime.now()
            new_restaurant = pd.DataFrame({"Restaurant": [self.restaurant_name], "Time Added": [current_time], "Time since added": [0]})
            df.to_csv('restaurants.txt', header=True, index=False)
            with open("restaurants.txt", "a") as rest_file:
                rest_file.write(f"{self.restaurant_name}, {current_time}, 0\n")
            df = pd.concat([df, new_restaurant], ignore_index=True)
            await channel.send((f"Adding restaurant: {self.restaurant_name}"))
            
class SeeRestaurants:
    def __init__(self, args):
        self.command = args[0]
    @bot.event
    async def execute(self, channel, args, df, line_count):
        await channel.send((f"Seeing restaurant\n"))
        table = tabulate(df, headers='keys', tablefmt='grid')
        text_bytes = table.encode('utf-8')
        text_io = BytesIO(text_bytes)
        await channel.send(file=discord.File(text_io, filename="message.txt"))

class RemoveRestaurants:
    def __init__(self, args):
        self.command = args[0]  
        if len(args) > 1 and "-c" in args:
            self.clear = True
        else:
            self.clear = False
    @bot.event
    async def execute(self, channel, args, df, line_count):
        if line_count == 0:
            await channel.send(("There are no restaurants to remove"))
            raise ValueError("There are no restaurants to remove")
        elif self.clear == True:
            df = pd.DataFrame()
            df.to_csv('restaurants.txt', header=True, index=False)
            await channel.send((f"Cleared all restaurants"))
        else:
            top = df.head(1)["Restaurant"].iloc[0]
            df = df[df.index != 0]
            df.to_csv('restaurants.txt', header=True, index=False)
            # Future development
            #lines = []
            #found = False
            #for line in rest_file:
            #    if self.restaurant_name not in line:
            #        lines.append(line.strip())
            #    elif found:
            #        lines.append(line.strip())
            #if not found:
            #    raise ValueError(f"There is no restaurant called {self.restaurant_name}")
            #for line in lines:
            #    rest_file.write(line + '\n')
            await channel.send((f"Removing restaurant: {top}"))

@bot.event
async def on_ready():
    guild_count = 0
    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1
    print(f"Sample discord bot is in {str(guild_count)} guilds")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Saving Pikastunner from mental despair one keystroke at a time 😋."))
    # Pikastunner channel
    #channel_id = 1124323950235754537

    # Other channel
    #channel_id = 1145338676470100118
    channel = bot.get_channel(channel_id)
    await channel.send("Hi user, I have come alive. Talk to me.")

def check_num(i):
    if i.isnumeric():
        return True
    else:
        try:
            float(i)
            return True
        except:
            return False
        
@bot.event      
async def add(channel, msg):
    both_nums = [i.replace(" ", "") for i in msg.content.split("+")]
    print([check_num(i) for i in both_nums])
    if len(both_nums) == 2 and all(check_num(i) for i in both_nums):
        both_nums = [float(i) for i in msg.content.split("+")]
        await channel.send(sum(both_nums))
    else:
        print(both_nums)

@bot.event
async def rand_resp(channel, msg):
    if msg.content == "Goodnight":
        await channel.send("I'll be waiting for you to improve me tomorrow. Goodnight adventurer. <:takuma:1132625527379857469>")
    if re.match("[W,w]ho is the gayest?", msg.content):
        names = ["Denton", "Catherine"]
        await channel.send(names[random.randint(0, len(names) - 1)])
    else:
        print(msg.content)
    if "2041" in msg.content:
        await channel.send("FL")
    else:
        print(msg.content)
    if "catherine" in msg.content and "mark" in msg.content:
        await channel.send("FL")
    if "denton" in msg.content and "mark" in msg.content:
        await channel.send("HD")

@bot.event
async def rest_stack(channel, args, handler, df, rest_commands, line_count):
    command = args[0]
    if command == "/add_restaurants":
        handler = AddRestaurants(args)
    elif command == "/see_restaurants":
        handler = SeeRestaurants(args)
    elif command == "/remove_restaurants":
        handler = RemoveRestaurants(args)
    else:
        help_df = pd.DataFrame(columns=["Commands", "Description"])
        instructions = pd.DataFrame({
            "Commands": rest_commands,
            "Description": [
                "Adds a restaurant into the stack.\nRequires a string argument that is enclosed in double quotation marks (\").\nFor example, /add_restaurants \"bite the dust\"",
                "Look at all the restaurants placed into the stack.\nDoes not need command line arguments.\nFor example, /see_restaurants",
                "Pops the restaurant that is at the top of the stack.\nApplying -c clears all restaurant entries.\nFor example, /remove_restaurants",
                "Displays a help menu.\nDoes not need command line arguments.\nFor example, /help_restaurants"
            ]
        })
        help_df = pd.concat([help_df, instructions], ignore_index=True)
        await channel.send("Help menu")
        table = tabulate(help_df, headers='keys', tablefmt='grid', showindex=False)
        text_bytes = table.encode('utf-8')
        text_io = BytesIO(text_bytes)
        await channel.send(file=discord.File(text_io, filename="message.txt"))
    if handler:
        await handler.execute(channel, args, df, line_count)   


async def make_timetable(channel, args, timetable_commands, existing_data):
    command = args[0]
    handler = False
    if command == "/add_user":
        handler = AddUser(args)
    elif command == "/select_user":
        handler = SelectUser(args)
    elif command == "/add_timetable":
        handler = AddTimetable(args)
    elif command == "/select_timetable":
        handler = SelectTimetable(args)
    elif command == "/add_course":
        handler = AddCourse(args)
    elif command == "/complete_term":
        handler = CompleteTerm(args)
    elif command == "/check_progression":
        handler = CheckProgression(args)
    elif command == "/visualise_timetable":
        handler = VisualiseTimetable(args)
    elif command == "/modify_user":
        handler = ModifyUser(args)
    elif command == "/drop_user":
        handler = DropUser(args)
    elif command == "/drop_year":
        handler = DropYear(args)
    elif command == "/drop_timetable":
        handler = DropTimetable(args)
    elif command == "/modify_course":
        handler = ModifyCourse(args)
    elif command == "/modify_completion":
        handler = ModifyCompletion(args)
    elif command == "/drop_course":
        handler = DropCourse(args)
    else:
        help_df = pd.DataFrame(columns=["Commands", "Description"])
        instructions = pd.DataFrame({
            "Commands": timetable_commands,
            "Description": [
                """Adds a user.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe first argument is the name of added user.\nThe second argument is the number of UoCs completed.\nThe last argument is the total number of UoCs the user has to complete.\nFor example, /add_user "Denton" "0" "100" """,
                """Selects a user that has been added.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe only argument is the name of selected user.\nFor example, /select_user "Denton" """,
                """Adds a timetable for a selected user.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe only argument is the year to create the timetable.\nFor example, /add_timetable "2023" """,
                """Selects a timetable for a selected user.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe first argument is the year of the to select timetable.\nThe last argument is the term of the to select timetable.\nFor example, /select_timetable "2023" "t2" """,
                """Adds a course for a selected user's timetable.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe first argument is the name of the course.\nThe second argument is the a set of days that a lab occurs.\nThe third argument is the a set of days that a tut occurs.\nThe last argument is the number of UoCs the course is worth.\nFor example, /add_course "MATH3821" "Monday 9:00-11:00, Friday 10:00-11:00" "Tuesday 16:00-18:00" "6" """,
                """Completes a term for a selected user's timetable.\nNo arguments are required.\nFor example, /complete_term """,
                """Check the progression of a user.\nNo arguments are required.\nFor example, /check_progression """,
                """Visualise a selected user's timetable.\nNo arguments are required.\nFor example, /visualise_timetable """,
                """Modifies a selected user's timetable.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe first argument is parameters to be changed seperated by a hyphen.\nThe last argument is the changes to those corresponding parameters also seperated by a hyphen.\nFor example, /modify_user "uocs_completed/total_uocs" "0/100" """,
                """Drops the selected user.\nNo arguments are required.\nFor example, /drop_user""",
                """Drop the selected year of the selected user.\nNo arguments are required.\nFor example, /drop_year""",
                """Drops the timetable of a selected year and timetable of a selected user.\nNo arguments are required.\nFor example, /timetable""",
                """Modifies a course of a selected year and timetable of a selected user.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe first argument is parameters to be changed seperated by a hyphen.\nThe last argument is the changes to those corresponding parameters also seperated by a hyphen.\nFor example, /modify_course /modify_course "COMP9444" "lab_days/tut_days/uocs" "Tuesday 3:00-4:00, Wednesday 4:00-5:00/Monday 9:00-10:00/6" """,
                """Modifies the completion status of a term.\nNo arguments are required.\nFor example, /modify_completion""",
                """Drops a course of a selected year and timetable of a selected user.\nRequires strings argument that is enclosed in double quotation marks (\").\nThe only argument is the name of the course to be dropped.\nFor example, /drop_course "COMP9444" """,
                """Displays a help menu.\nNo arguments are required.\nFor example, /help_timetable"""
            ]
        })
        help_df = pd.concat([help_df, instructions], ignore_index=True)
        await channel.send("Timetable Help Menu")
        table = tabulate(help_df, headers='keys', tablefmt='grid', showindex=False)
        text_bytes = table.encode('utf-8')
        text_io = BytesIO(text_bytes)
        await channel.send(file=discord.File(text_io, filename="message.txt"))
    if handler:
        await handler.execute(channel, args, existing_data)     

async def log_event(channel, args):
    df = pd.read_csv("timeline.csv")
    time = args[1]
    event = args[2]
    reason = args[3]
    new_row = {"Date": time, "Event": event, "Reason": reason}
    df = df.append(new_row, ignore_index=True)
    df.to_csv('timeline.csv', index=False)
    await channel.send("Row successfully appended")


@bot.event
async def on_message(msg):
    # Pikastunner server
    #guild_id = 1110051126071533649
    #channel_id = 1124323950235754537
    
    # Other server
    #guild_id = 1106222465618825328
    #channel_id = 1145338676470100118

    with open("start.json", "r") as json_file:
        listen = json.load(json_file)["Listen"]

    channel = bot.get_channel(channel_id)
    if msg.guild is not None and msg.guild.id == guild_id and msg.channel.id == channel_id and not msg.author.bot:
        if msg.content == "/deafen":
            with open("start.json", "w") as json_file:
                data = {"Listen": False}
                json.dump(data, json_file, indent=4)
            await channel.send("I am deafened to your messages.")
        elif (msg.content == "/listen" and listen == False) or listen == True:
            if not listen:
                with open("start.json", "w") as json_file:
                    data = {"Listen": not listen}
                    json.dump(data, json_file, indent=4)
                await channel.send("I am all ears for you.")
            elif msg.content == "/listen":
                await channel.send("I can hear you already.")

            await add(channel, msg)  
            await rand_resp(channel, msg)

            # Command list
            args = msg.content.split(" ")
            rest_commands = ["/add_restaurants", "/see_restaurants", "/remove_restaurants", "/help_restaurants"]
            timetable_commands = [
                "/add_user", "/select_user", "/add_timetable", "/select_timetable",
                "/add_course", "/complete_term", "/check_progression", "/visualise_timetable", "/modify_user", "/drop_user", 
                "/drop_year", "/drop_timetable", "/modify_completion", "/modify_course", "/drop_course", "/help_timetable"]

            # Format Check
            arg_string = re.sub(rf'{args[0]}', '', msg.content)
            if len(arg_string) > 0 and arg_string[1] != "\"":     
                print(f"HERE IS THE {repr(arg_string)}")   
                await channel.send("Please encase your string commands with double quotation marks (\")")
                raise ValueError("Please encase your string commands with double quotation marks (\")")
            args = [i[:-1] if i[-1] == "\"" else i for i in re.split("\s\"", msg.content)]
            print(f"{args} is args")

            # Commands
            if args[0] in rest_commands:
                print("IS A COMMAND")
                handler = None
                line_count = 0
                to_df = []
                with open("restaurants.txt", "r") as rest_file:
                    for line in rest_file:
                        line_count += 1
                        to_df.append(line.strip().split(","))
                print(f"LINE COUNT IS {line_count}")
                to_df = to_df[1:]
                df = pd.DataFrame(to_df, columns=["Restaurant", "Time Added", "Time since added"])
                df['Time Added'] = pd.to_datetime(df['Time Added'])
                df["Time since added"] = datetime.now() - df["Time Added"]
                await rest_stack(channel, args, handler, df, rest_commands, line_count)
            elif args[0] in timetable_commands:
                print("IS A COMMAND")
                try:
                    with open("users.json", "r") as users_json:
                        existing_data = json.load(users_json)
                except:
                    existing_data = {
                        "Users": {},
                        "Selected_user": "",
                        "Selected_timetable": []
                    }
                await make_timetable(channel, args, timetable_commands, existing_data)
                pass
            else:
                if args[0] == "/log_time":
                    await log_event(channel, args)
                elif args[0] == "/logoff":
                    print("IS A COMMAND")
                    await channel.send("Goodbye I will see you soon")
                    sys.exit()
                else:
                    print(f"{repr(args[0])} IS NOT A COMMAND")

# Pikastunner server
#bot.run("MTEyNDMxMTUwODkyNzY2NDE0OQ.GQkAcz._ZEnifs8vbzy1jbLA_chlX-7eshPMLe-TgrUyA")
bot.run(token)
# Other server
#bot.run("MTE0MDI5OTg1ODUyMDA2NDAxMA.GTf4mg.MSLeD7pZfZIfBWd6iGOY7h9S4aDd6rOfs6pTBE")