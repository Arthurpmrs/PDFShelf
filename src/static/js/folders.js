(function () {
    // Constants and elements - COLOCAR TUDO NUM OBJECTO SÓ
    const addFolderModal = document.querySelector("#add-folder-modal");
    const addFolderCloseButton = document.querySelector(
        "#add-folder-modal .modal-close"
    );
    const addFolderButton = document.querySelector("#add-folder");
    const openAddFolderModel = document.querySelector("#open-add-modal");
    const addFolderInputs = addFolderModal.querySelectorAll("input");
    let ERROR_STATUS = false;

    // event listeners for folders.html - COLOCAR NUM OBJETO
    openAddFolderModel.addEventListener("click", () => {
        addFolderModal.showModal();
    });

    addFolderButton.addEventListener("click", () => {
        post_add_folder();
    });

    addFolderCloseButton.addEventListener("click", () => {
        addFolderModal.close();
    });

    addFolderInputs.forEach((input) => {
        input.addEventListener("focus", () => {
            if (ERROR_STATUS) {
                reset_modal(addFolderModal);
                ERROR_STATUS = false;
            }
        });
    });

    // methods
    function post_add_folder() {
        const name_input = addFolderModal.querySelector("#add-folder-name");
        const path_input = addFolderModal.querySelector("#add-folder-path");
        const folder_data = {
            name: name_input.value,
            path: path_input.value,
        };
        console.log(folder_data);

        fetch("/folders/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(folder_data),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success === true) {
                    path_input.value = "";
                    name_input.value = "";
                    window.location.reload();
                } else {
                    set_modal_error_state(data.message);
                }
            });
    }

    function set_modal_error_state(message) {
        const modalMessage = addFolderModal.querySelector(".message");
        modalMessage.innerText = message;
        addFolderButton.classList.add("error");
        ERROR_STATUS = true;
    }

    function reset_modal(modal) {
        modal.querySelector("#add-folder").classList.remove("error");
        modal.querySelector(".message").innerText = "";
    }
})();
