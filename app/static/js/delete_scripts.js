function reloadPageAndParent() { // for iframes
    parent.location.reload();
};

function deleteComponentAndReload(component_id) {
    // For iframes - deletes the component with the given component_id and reloads the parent page
    if (confirm("Are you sure you want to delete this component?")) {
        fetch("/delete_component/" + component_id, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())  // Parse the response as JSON
        .then(data => {
            if (data.success) {
                // If deletion was successful, reload the page and parent
                reloadPageAndParent();
            } else {
                alert(data.message || "Failed to delete the component.");
            }
        }).catch(error => {
            console.error("Error during deletion:", error);
            alert("An error occurred while trying to delete the component.");
        });
    }
};

function deleteTrip(trip_id, reload=true) { 
    // function will send a POST request to the server to delete the trip with the given trip_id
    // if reload is false, the page will redirect to homepage
    if (confirm("Are you sure you want to delete this trip?")) {
        fetch("/delete_trip/" + trip_id, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())  // Parse the response as JSON
        .then(data => {
            if (data.success) {
                if (reload) {
                    window.location.reload();
                } else {
                    window.location.href = "/";
                }
            } else {
                alert(data.message || "Failed to delete the trip.");
            }
        }).catch(error => {
            console.error("Error during deletion:", error);
            alert("An error occurred while trying to delete the trip.");
        });
    }
};

function setNewEditedComponent(trip_id) {
    const edit_component = document.getElementById('edit-component');
    if (edit_component) {
        edit_component.innerHTML = '<iframe class="edit-component" src="/create_component/' + trip_id + '"></iframe>';
    }
}
function changeEditedComponent(component_id) {
    const edit_component = document.getElementById('edit-component');
    if (edit_component) {
        edit_component.innerHTML = '<iframe class="edit-component" src="/component/' + component_id + '"></iframe>';
    }
}