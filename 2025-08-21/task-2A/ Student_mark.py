# Student Record System (CSE Department)

# 1. Subjects (5 including Computer Science)
subjects = ("Maths", "Chemistry", "English", "Computer Science", "Physics")

# 2. Student details (5 students, one failing case)
students = [
    {"name": "Rahul", "age": 18, "marks": [75, 60, 82, 90, 68]},  
    {"name": "Sneha", "age": 19, "marks": [55, 48, 50, 62, 59]},  
    {"name": "Afsal", "age": 18, "marks": [35, 28, 40, 30, 25]},   
    {"name": "Priya", "age": 20, "marks": [85, 92, 78, 88, 80]},  
    {"name": "Kiran", "age": 19, "marks": [60, 72, 68, 74, 70]}   
]

# 3. Loop through students and generate report
for student in students:
    name = student["name"]
    age = student["age"]
    marks = student["marks"]

    # Calculate total and average
    total = sum(marks)
    average = total / len(marks)

    # Pass or Fail
    if average >= 40:
        result = "Passed"
        is_passed = True
    else:
        result = "Failed"
        is_passed = False

    # Print Student Report
    print("===== CSE Student Report =====")
    print("Name:", name)
    print("Age:", age)
    print("Subjects:", subjects)
    print("Marks:", marks)
    print("Total Marks:", total)
    print("Average Marks:", round(average, 2))
    print("Result:", result)
    print("==============================\n")