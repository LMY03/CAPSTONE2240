let sectionCounts = {};
let addCourseSectionClicked = 1;


function formatDate(date) {
    const d = new Date(date);
    let month = '' + (d.getMonth() + 1);
    let day = '' + d.getDate();
    const year = d.getFullYear();

    if (month.length < 2)
        month = '0' + month;
    if (day.length < 2)
        day = '0' + day;

    return [year, month, day].join('-');
}

document.getElementById('use_case').addEventListener('change', function () {
    let classCourseInput = document.getElementById('class_course_input');
    if (this.value === 'CLASS_COURSE') {
        classCourseInput.style.display = 'block';
    } else {
        classCourseInput.style.display = 'none';
    }
});


document.getElementById('useroption').addEventListener('change', function () {
    let use_case = document.getElementById('use_case');
    let studentgroup = document.getElementById('studentgroup');
    let studentIndividual = document.getElementById('individual_student_container');

    if (use_case.value === 'CLASS_COURSE' && this.value === 'group') {
        studentgroup.innerHTML = '';
        studentgroup.style.display = 'block';
        studentIndividual.style.display = 'none';

        for (let i = 0; i < addCourseSectionClicked; i++) {
            const courseCodeInput = document.getElementById(`course_code${i + 1}`);
            const section_code = courseCodeInput?.value.toString().split("_")?.[1];
            let newGroupCounter = 0;
            if (section_code) {
                if (!sectionCounts[section_code]) {
                    sectionCounts[section_code] = {
                        "GroupCounter": 1
                    };
                }
                const sectionDiv = document.createElement('div');
                sectionDiv.id = `section_${section_code}`;
                const newLabel = document.createElement('label');
                newLabel.innerHTML = `<br>${section_code} Group 1:`;

                const newTextArea = document.createElement('textarea');
                newTextArea.className = 'form-control';
                newTextArea.name = `student_user_${section_code}_1`;
                newTextArea.id = `student_user_${section_code}_1`;
                newTextArea.rows = 3;

                const newButton = document.createElement('button');
                newButton.innerText = 'Add Group';
                newButton.type = 'button';
                newButton.addEventListener('click', function () {
                    const newSectionDiv = document.createElement('div');
                    newSectionDiv.id = `div_${section_code}_Group${newGroupCounter}`


                    newGroupCounter = ++sectionCounts[section_code]["GroupCounter"];
                    const newLabel = document.createElement('label');
                    newLabel.innerHTML = `<br>${section_code} Group ${newGroupCounter}:`;
                    newLabel.id = `label_${section_code}_Group${newGroupCounter}`
                    const newTextArea = document.createElement('textarea');
                    newTextArea.className = 'form-control';
                    newTextArea.name = `student_user_${section_code}_${newGroupCounter}`;
                    newTextArea.id = `student_user_${section_code}_${newGroupCounter}`;
                    newTextArea.rows = 3;

                    const newRemoveButton = document.createElement('button');
                    newRemoveButton.innerText = '-';
                    newRemoveButton.type = 'button';
                    newRemoveButton.addEventListener('click', function () {
                        newSectionDiv.remove()
                        sectionCounts[section_code]["GroupCounter"] = sectionCounts[section_code]["GroupCounter"] - 1;
                    })
                    newSectionDiv.appendChild(newLabel);
                    newSectionDiv.appendChild(newTextArea);
                    newSectionDiv.appendChild(newRemoveButton);
                    sectionDiv.append(newSectionDiv);
                });

                sectionDiv.appendChild(newLabel);
                sectionDiv.appendChild(newTextArea);
                sectionDiv.appendChild(newButton);
                studentgroup.appendChild(sectionDiv);
            }
        }
    } else {
        studentIndividual.style.display = 'block';
        studentgroup.style.display = 'none';
    }
});

document.getElementById('add_course_button').addEventListener('click', () => {
    addCourseSectionClicked++;
    let use_case = document.getElementById('use_case');

    if (use_case.value === 'CLASS_COURSE') {
        var inputContainer = document.getElementById('class_course_input');
        var newInput = document.createElement('input');
        let newLabel = document.createElement('label');
        newLabel.innerHTML = `<br>Course Code ${addCourseSectionClicked} with section:`
        newInput.type = 'text';
        newInput.className = 'form-control w-25';
        newInput.name = `course_code${addCourseSectionClicked}`;
        newInput.id = `course_code${addCourseSectionClicked}`
        inputContainer.appendChild(newLabel);
        inputContainer.appendChild(newInput);

    }
});


// Submit the form
document.getElementById('vm-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    const formInputs = this.querySelectorAll('input[type="text"], select, textarea, input[type="number"], input[type="date"]');
    const formDataInputs = Object.fromEntries(Array.from(formInputs).map(input => [input.id, input.value]));
    for (let sectionCode in sectionCounts) {
        const groupCount = sectionCounts[sectionCode]["GroupCounter"]
        formDataInputs[`${sectionCode}_group_count`] = groupCount;
        formData.append(`sections`, sectionCode)
        formData.append(`${sectionCode}_group_count`, formDataInputs[`${sectionCode}_group_count`]);
    }
    formDataInputs[`addCourseButtonClick`] = addCourseSectionClicked;
    formData.append('addCourseButtonClick', formDataInputs[`addCourseButtonClick`])
    //formData.append()
    fetch(this.action, {
        method: this.method,
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // Handle the response from the backend
            //console.log(data);
        })
        .catch(error => {
            console.log(error)
        })
});

// Set the min and max dates
window.onload = function () {
    const today = new Date();
    const dateNeededMin = new Date(today);
    dateNeededMin.setDate(today.getDate() + 3); // 3 days from today

    const expirationDateMax = new Date(today);
    const expirationDateMin = new Date(today);
    expirationDateMax.setFullYear(today.getFullYear() + 1); // 1 year from today
    expirationDateMin.setMonth(today.getMonth() + 3);

    document.getElementById('date_needed').setAttribute('min', formatDate(dateNeededMin));
    document.getElementById('expiration_date').setAttribute('max', formatDate(expirationDateMax));
    document.getElementById('expiration_date').setAttribute('min', formatDate(expirationDateMin));
}