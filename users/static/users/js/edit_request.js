let sectionCounts = {};
let addCourseSectionClicked = 1;
let useCaseIsChanged = 0;
if (sectionsData.length !== 0) {
    addCourseSectionClicked = sectionsData.length;
    console.log('sectionsData is not empty')
}

console.log(portRules)
let newAddedGroup = {};

// for (let section in sectionsData) {
//     let counter = 2;
//     let sectionData = sectionsData[section];
//     let sectionCountKey = `${section} Group Count`;
//     let newAddedGroup = {
//         [sectionCountKey]: Object.keys(section).length
//     };
//     document.getElementById(`add_group_button${section}`).addEventListener('click', function () {
//         let parentDiv = document.getElementById(`section_${section}`);

//         const newLabel = document.createElement('label');
//         newLabel.innerHTML = `<br>${section} Group ${++newAddedGroup[sectionCountKey]}:`;

//         const newTextArea = document.createElement('textarea');
//         newTextArea.className = 'form-control';
//         newTextArea.name = `student_user_${section}_${newAddedGroup[sectionCountKey]}`;
//         newTextArea.id = `student_user_${section}_${newAddedGroup[sectionCountKey]}`;
//         newTextArea.rows = 3;

//         parentDiv.appendChild(newLabel);
//         parentDiv.appendChild(newTextArea);
//     });

//     for (let group in sectionData) {

//         console.log(`remove_group_${section}_${counter}`)
//         if (group != 'Group 1') {
//             document.getElementById(`remove_group_${section}_${counter}`).addEventListener('click', function () {
//                 console.log(`div_${section}_${group}, student_user_${section}_${counter}`);
//                 let divSectionGroup = document.getElementById(`div_${section}_${group}`);
//                 let textAreaSectionGroup = document.getElementById(`student_user_${section}_${counter - 1}`);
//                 if (textAreaSectionGroup) {
//                     textAreaSectionGroup.remove();
//                 }
//                 if (divSectionGroup) {
//                     divSectionGroup.remove();
//                 }
//             });
//             counter += 1;
//         }

//     }
// }

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

    if (use_case === 'CLASS_COURSE' && useCaseIsChanged == 0) {
        useCaseIsChanged = 1;
        let vmCountLabel = document.createElement('label');
        vmCountLabel.setAttribute('for', 'vm_count1');
        vmCountLabel.setAttribute('class', 'form-label');
        vmCountLabel.textContent = 'VM Count:';

        let vm_and_coursecode = document.getElementById('vm_and_coursecode')
        document.getElementById('vm_count1_div').remove()
        vmCountInput = document.createElement('input');
        vmCountInput.setAttribute('type', 'number');
        vmCountInput.setAttribute('id', 'vm_count1');
        vmCountInput.setAttribute('name', 'vm_count1');
        vmCountInput.setAttribute('min', '1');
        vmCountInput.setAttribute('max', '40');
        vm_and_coursecode.appendChild(vmCountLabel);
        vm_and_coursecode.appendChild(vmCountInput);
    }
    if (this.value === 'CLASS_COURSE') {
        classCourseInput.style.display = 'block';
    } else {
        classCourseInput.style.display = 'none';
    }
});



document.getElementById('add_course_button').addEventListener('click', () => {
    addCourseSectionClicked++;
    let use_case = document.getElementById('use_case');

    if (use_case.value === 'CLASS_COURSE') {
        var inputContainer = document.getElementById('vm_and_coursecode');
        var newInput = document.createElement('input');
        let newLabel = document.createElement('label');

        newLabel.innerHTML = `Course Code ${addCourseSectionClicked} with section:`
        newInput.type = 'text';
        newInput.className = 'form-control w-25';
        newInput.name = `course_code${addCourseSectionClicked}`;
        newInput.id = `course_code${addCourseSectionClicked}`

        const newCourseDiv = document.createElement('div');

        newCourseDiv.classList.add('mb-3');

        const newVMLabel = document.createElement('label');
        const newVMInput = document.createElement('input');

        newVMLabel.innerHTML = `VM Count for section ${addCourseSectionClicked}: `
        newVMInput.type = 'number'
        newVMInput.id = `vm_count${addCourseSectionClicked}`

        const newVMDiv = document.createElement('div');

        newVMDiv.classList.add('mb-3');
        newVMDiv.appendChild(newVMLabel);
        newVMDiv.appendChild(newVMInput);

        const removeCourseBtn = document.createElement('button');
        removeCourseBtn.type = 'button';
        removeCourseBtn.classList.add('btn', 'btn-outline-danger');
        removeCourseBtn.innerHTML = 'Remove Course';
        removeCourseBtn.addEventListener('click', function () {
            newCourseDiv.remove();
            newVMDiv.remove()
            addCourseSectionClicked--;
        });

        const newCourseLabelDiv = document.createElement('div');
        newCourseLabelDiv.classList.add('d-flex', 'justify-content-between')

        newCourseLabelDiv.append(newLabel);
        newCourseLabelDiv.append(removeCourseBtn);

        newCourseDiv.append(newCourseLabelDiv);
        newCourseDiv.appendChild(newInput);

        inputContainer.appendChild(newCourseDiv);
        inputContainer.appendChild(newVMDiv);
    }
});


// Submit the form
document.getElementById('vm-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    const formInputs = this.querySelectorAll('input[type="text"], select, textarea, input[type="number"], input[type="date"]');
    const formDataInputs = Object.fromEntries(Array.from(formInputs).map(input => [input.id, input.value]));
    // for (let sectionCode in sectionCounts) {
    //     const groupCount = sectionCounts[sectionCode]["GroupCounter"]
    //     formDataInputs[`${sectionCode}_group_count`] = groupCount;
    //     formData.append(`sections`, sectionCode)
    //     formData.append(`${sectionCode}_group_count`, formDataInputs[`${sectionCode}_group_count`]);
    // }
    formDataInputs[`addCourseButtonClick`] = addCourseSectionClicked;
    formDataInputs[`id`] = requestID;

    if (addCourseSectionClicked != 0) {
        formDataInputs['sections'] = sectionsData;
    }

    if (portRules != []) {
        formDataInputs['port_rules'] = portRules;
    }

    console.log(formDataInputs['port_rules'])
    console.log(formDataInputs['request_use_case'])
    for (const key in formDataInputs) {
        formData.append(key, formDataInputs[key])
    }
    console.log(formDataInputs);
    fetch(this.action, {
        method: this.method,
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                // Redirect to a different page
                window.location.href = '/users/faculty/home';
            } else {
                // Handle other statuses if needed
                console.log('Unexpected status:', data.status);
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
});

for (let index = 2; index <= sectionsData.length; index++) {
    document.getElementById(`remove_section_button${index}`).addEventListener('click', function () {
        document.getElementById(`section_vm_count_${index}`).remove()
        addCourseSectionClicked--;
    });
}



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

    document.getElementById('external_access').addEventListener('change', function () {
        let networkAccordion = document.getElementById('networkAccordion');
        if (this.value == 'true') {
            networkAccordion.style.display = 'block';
        } else {
            networkAccordion.style.display = 'none';
        }
    });
}
