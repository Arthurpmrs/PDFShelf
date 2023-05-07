// event listeners for folders.html
document.querySelector("#add-folder-button").addEventListener("click", () => {
    post_add_folder();
});

// methods
function post_add_folder() {
    const path_input = document.querySelector("#path-input");
    const path = path_input.value;

    fetch("/folders/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            if (data.success) {
                path_input.value = "";
                window.location.reload();
            } else {
                alert("Something went wrong.");
            }
        });
}
