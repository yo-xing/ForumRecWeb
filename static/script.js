// function openTab(evt, tabName) {
//     // Declare all variables
//     var i, tabcontent, tablinks;
  
//     // Get all elements with class="tabcontent" and hide them
//     tabcontent = document.getElementsByClassName("tabcontent");
//     for (i = 0; i < tabcontent.length; i++) {
//       tabcontent[i].style.display = "none";
//     }
  
//     // Get all elements with class="tablinks" and remove the class "active"
//     tablinks = document.getElementsByClassName("tablinks");
//     for (i = 0; i < tablinks.length; i++) {
//       tablinks[i].className = tablinks[i].className.replace(" active", "");
//     }
  
//     // Show the current tab, and add an "active" class to the button that opened the tab
//     document.getElementById(tabName).style.display = "block";
//     evt.currentTarget.className += " active";
//   }

// Opens Tab on defualt
// document.getElementById('defaultTab').click();

function letSubmit() {
    // Get checkboxes list and submit button
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    let submitter = document.getElementById('submit_button');

    if (Array.prototype.slice.call(checkboxes).filter(x => x.checked == true).length >= 10) {
      submitter.disabled = false;
    }
    else {
      submitter.disabled = true;
    }

}

// https://www.w3schools.com/howto/howto_js_tabs.asp