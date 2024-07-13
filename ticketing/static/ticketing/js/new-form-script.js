let sectionCounts = {};
let addCourseSectionClicked = 1;
let addProtocolClicked = 1;


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


// document.getElementById('useroption').addEventListener('change', function () {
//     let use_case = document.getElementById('use_case');
//     let studentgroup = document.getElementById('studentgroup');
//     let studentIndividual = document.getElementById('individual_student_container');

//     if (use_case.value === 'CLASS_COURSE' && this.value === 'group') {
//         studentgroup.innerHTML = '';
//         studentgroup.style.display = 'block';
//         studentIndividual.style.display = 'none';

//         for (let i = 0; i < addCourseSectionClicked; i++) {
//             const courseCodeInput = document.getElementById(`course_code${i + 1}`);
//             const section_code = courseCodeInput?.value.toString().split("_")?.[1];
//             let newGroupCounter = 0;
//             if (section_code) {
//                 if (!sectionCounts[section_code]) {
//                     sectionCounts[section_code] = {
//                         "GroupCounter": 1
//                     };
//                 }
//                 const sectionDiv = document.createElement('div');
//                 sectionDiv.id = `section_${section_code}`;
//                 const newLabel = document.createElement('label');
//                 newLabel.innerHTML = `<br>${courseCodeInput} Group 1:`;

//                 const newTextArea = document.createElement('textarea');
//                 newTextArea.className = 'form-control';
//                 newTextArea.name = `student_user_${section_code}_1`;
//                 newTextArea.id = `student_user_${section_code}_1`;
//                 newTextArea.rows = 3;

//                 const newButton = document.createElement('button');
//                 newButton.innerText = 'Add Group';
//                 newButton.type = 'button';
//                 newButton.addEventListener('click', function () {
//                     const newSectionDiv = document.createElement('div');
//                     newSectionDiv.id = `div_${section_code}_Group${newGroupCounter}`


//                     newGroupCounter = ++sectionCounts[section_code]["GroupCounter"];
//                     const newLabel = document.createElement('label');
//                     newLabel.innerHTML = `<br>${courseCodeInput} Group ${newGroupCounter}:`;
//                     newLabel.id = `label_${section_code}_Group${newGroupCounter}`
//                     const newTextArea = document.createElement('textarea');
//                     newTextArea.className = 'form-control';
//                     newTextArea.name = `student_user_${section_code}_${newGroupCounter}`;
//                     newTextArea.id = `student_user_${section_code}_${newGroupCounter}`;
//                     newTextArea.rows = 3;

//                     const newRemoveButton = document.createElement('button');
//                     newRemoveButton.innerText = '-';
//                     newRemoveButton.type = 'button';
//                     newRemoveButton.addEventListener('click', function () {
//                         newSectionDiv.remove()
//                         sectionCounts[section_code]["GroupCounter"] = sectionCounts[section_code]["GroupCounter"] - 1;
//                     })
//                     newSectionDiv.appendChild(newLabel);
//                     newSectionDiv.appendChild(newTextArea);
//                     newSectionDiv.appendChild(newRemoveButton);
//                     sectionDiv.append(newSectionDiv);
//                 });

//                 sectionDiv.appendChild(newLabel);
//                 sectionDiv.appendChild(newTextArea);
//                 sectionDiv.appendChild(newButton);
//                 studentgroup.appendChild(sectionDiv);
//             }
//         }
//     } else {
//         studentIndividual.style.display = 'block';
//         studentgroup.style.display = 'none';
//     }
// });

document.getElementById('add_course_button').addEventListener('click', () => {
    addCourseSectionClicked++;
    let use_case = document.getElementById('use_case');

    if (use_case.value === 'CLASS_COURSE') {
        var inputContainer = document.getElementById('vm_and_coursecode');
        var newInput = document.createElement('input');
        let newLabel = document.createElement('label');

        newLabel.innerHTML = `<span>Course Code ${addCourseSectionClicked} with section:</span>`
        newInput.type = 'text';
        newInput.className = 'form-control w-25';
        newInput.name = `course_code${addCourseSectionClicked}`;
        newInput.id = `course_code${addCourseSectionClicked}`

        const newCourseDiv = document.createElement('div');
        const newLabelButtonDiv = document.createElement('div');
        newLabelButtonDiv.classList.add('d-flex', 'justify-content-between', 'align-items-center');
        newLabelButtonDiv.append(newLabel);



        const removeCourseBtn = document.createElement('button');
        removeCourseBtn.type = 'button';
        removeCourseBtn.classList.add('btn', 'btn-outline-danger');
        removeCourseBtn.innerHTML = 'Remove Course';

        newCourseDiv.classList.add('mb-3');
        newLabelButtonDiv.appendChild(removeCourseBtn);
        newCourseDiv.appendChild(newLabelButtonDiv);
        newCourseDiv.appendChild(newInput);

        const newVMLabel = document.createElement('label');
        const newVMInput = document.createElement('input');

        newVMLabel.innerHTML = `VM Count for section ${addCourseSectionClicked}: `
        newVMInput.type = 'number'
        newVMInput.id = `vm_count${addCourseSectionClicked}`

        const newVMDiv = document.createElement('div');

        newVMDiv.classList.add('mb-3');
        newVMDiv.appendChild(newVMLabel);
        newVMDiv.appendChild(newVMInput);


        inputContainer.appendChild(newCourseDiv);
        inputContainer.appendChild(newVMDiv);


        removeCourseBtn.addEventListener('click', function () {
            newCourseDiv.remove();
            newVMDiv.remove()
            addCourseSectionClicked--;
        });
    }
});


// Submit the form
document.getElementById('vm-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    const formInputs = this.querySelectorAll('input[type="text"], select, textarea, input[type="number"], input[type="date"]');
    const formDataInputs = {};
    let i = 1, j = 1;
    formInputs.forEach(input => {
        formDataInputs[input.id] = input.value;
        if (input.id.startsWith('protocol')) {
            let protocolNumber = input.id.replace('protocol', '');
            formDataInputs[`addProtocolClicked`] = '';
            formDataInputs[`addProtocolClicked`] = protocolNumber;
            i++;
        }
        if (input.id.startsWith('course_code')) {
            let courseCodeNumber = input.id.replace('course_code', '');
            formDataInputs[`addCourseButtonClick`] = '';
            formDataInputs[`addCourseButtonClick`] = courseCodeNumber;
        }

    });
    // for (let sectionCode in sectionCounts) {
    //     const groupCount = sectionCounts[sectionCode]["GroupCounter"]
    //     formDataInputs[`${sectionCode}_group_count`] = groupCount;
    //     formData.append(`sections`, sectionCode)
    //     formData.append(`${sectionCode}_group_count`, formDataInputs[`${sectionCode}_group_count`]);
    // }



    for (const key in formDataInputs) {
        formData.append(key, formDataInputs[key]);
    }
    console.log(formData);
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
                window.location.href = '/ticketing/';
            } else {
                // Handle other statuses if needed
                console.log('Unexpected status:', data.status);
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
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

document.getElementById('external_access').addEventListener('change', function () {
    console.log('external access changed')
    let networkAccordion = document.getElementById('networkAccordion');
    if (this.value == 'true') {
        networkAccordion.style.display = 'block';
    } else {
        networkAccordion.style.display = 'none';
    }
});


document.getElementById('addProtocolButton').addEventListener('click', function () {
    addProtocolClicked++;
    let accordion = document.getElementById('accordionBody_networkDetails');

    const newDivProtocol = document.createElement('div');
    newDivProtocol.classList.add('mb-3', 'protocol-group');
    newDivProtocol.id = `protocolGroup${addProtocolClicked}`;

    const newProtocolLabel = document.createElement('label');
    newProtocolLabel.innerHTML = `Protocol ${addProtocolClicked}:`;
    newProtocolLabel.classList.add('form-label');
    newProtocolLabel.setAttribute('for', `protocol${addProtocolClicked}`);

    const newProtocolSelect = document.createElement('select');
    newProtocolSelect.className = 'form-control';
    newProtocolSelect.id = `protocol${addProtocolClicked}`;
    newProtocolSelect.name = `protocol${addProtocolClicked}`;

    let options = [
        { value: 'tcp', text: 'TCP' },
        { value: 'udp', text: 'UDP' },
        { value: 'tcp/udp', text: 'TCP/UDP' },
    ];

    options.forEach(function (option) {
        let opt = document.createElement('option');
        opt.value = option.value;
        opt.text = option.text;
        newProtocolSelect.appendChild(opt);
    });

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.classList.add('btn', 'btn-danger');
    removeButton.innerText = 'Remove';
    removeButton.addEventListener('click', function () {
        accordion.removeChild(newDivProtocol);
        accordion.removeChild(newDivDestination);
        addProtocolClicked--;
    });

    const labelDiv = document.createElement('div');
    labelDiv.classList.add('d-flex', 'align-items-center', 'justify-content-between', 'mb-3');
    labelDiv.appendChild(newProtocolLabel);
    labelDiv.appendChild(removeButton);

    newDivProtocol.appendChild(labelDiv);
    newDivProtocol.appendChild(newProtocolSelect);

    const newDivDestination = document.createElement('div');
    newDivDestination.classList.add('mb-3');
    newDivDestination.id = `destinationGroup${addProtocolClicked}`;
    const newDestinationPortLabel = document.createElement('label');
    newDestinationPortLabel.innerHTML = `Destination Port ${addProtocolClicked}:`;
    newDestinationPortLabel.classList.add('form-label');
    newDestinationPortLabel.setAttribute('for', `destination_port${addProtocolClicked}`);

    const newDestinationPortInput = document.createElement('input');
    newDestinationPortInput.type = 'text';
    newDestinationPortInput.className = 'form-control';
    newDestinationPortInput.id = `destination_port${addProtocolClicked}`;
    newDestinationPortInput.name = `destination_port${addProtocolClicked}`;

    newDivDestination.appendChild(newDestinationPortLabel);
    newDivDestination.appendChild(newDestinationPortInput);

    accordion.appendChild(newDivProtocol);
    accordion.appendChild(newDivDestination);
});
