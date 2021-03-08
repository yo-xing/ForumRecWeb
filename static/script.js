function letSubmit() {
    // Get checkboxes list and submit button
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    let submitter = document.getElementById('submit_button');

    // Check if 10 boxes are clicked, and allows submission if so
    if (Array.prototype.slice.call(checkboxes).filter(x => x.checked == true).length >= 10) {
      submitter.disabled = false;
    }
    else {
      submitter.disabled = true;
    }

}