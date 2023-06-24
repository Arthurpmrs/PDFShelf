(function () {
    // General constants and elements
    let ERROR_STATUS = {
        add: false,
        edit: false,
        delete: false,
    };

    // Add folder
    const addFolderModal = document.querySelector("#add-folder-modal");
    const openAddFolderModel = document.querySelector("#open-add-modal");
    openAddFolderModel.addEventListener("click", () => {
        addFolderModal.showModal();
    });

    const addFolderButton = document.querySelector("#add-folder");
    addFolderButton.addEventListener("click", () => {
        post_add_folder();
    });

    const addFolderCloseButton = document.querySelector(
        "#add-folder-modal .modal-close"
    );
    addFolderCloseButton.addEventListener("click", () => {
        addFolderModal.close();
    });

    const addFolderInputs = addFolderModal.querySelectorAll("input");
    addFolderInputs.forEach((input) => {
        input.addEventListener("focus", () => {
            if (ERROR_STATUS.add === true) {
                reset_modal(addFolderModal);
                ERROR_STATUS.add = false;
            }
        });
    });

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
                    set_modal_error_state(addFolderModal, data.message, "add");
                }
            });
    }

    // Edit
    const editFolderModal = document.querySelector("#edit-folder-modal");
    const editButtons = document.querySelectorAll("button.edit");
    editButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setup_edit_modal(button.parentElement.parentElement);
            editFolderModal.showModal();
        });
    });

    const editFolderCloseButton = document.querySelector(
        "#edit-folder-modal .modal-close"
    );
    editFolderCloseButton.addEventListener("click", () => {
        editFolderModal.close();
    });

    const editFolderInputs = editFolderModal.querySelectorAll("input");
    editFolderInputs.forEach((input) => {
        input.addEventListener("focus", () => {
            if (ERROR_STATUS.edit === true) {
                reset_modal(editFolderModal);
                ERROR_STATUS.edit = false;
            }
        });
    });

    function setup_edit_modal(folder_card) {
        const name_input = editFolderModal.querySelector("#edit-folder-name");
        const path_input = editFolderModal.querySelector("#edit-folder-path");
        const title = editFolderModal.querySelector("h2");

        const folder_name = folder_card.querySelector(".name").innerText;
        const folder_path = folder_card.querySelector(".path").innerText;
        const folder_id = folder_card.id;

        title.innerText = `Edit ${folder_name} (id=${folder_id})`;

        name_input.value = folder_name;
        path_input.value = folder_path;

        const editFolderButton = editFolderModal.querySelector("#edit-folder");
        editFolderButton.addEventListener(
            "click",
            () => {
                post_edit_folder(folder_id);
            },
            { once: true }
        );
    }

    function post_edit_folder(folder_id) {
        const name_input = editFolderModal.querySelector("#edit-folder-name");
        const path_input = editFolderModal.querySelector("#edit-folder-path");

        const folder_data = {
            name: name_input.value,
            path: path_input.value,
        };

        fetch(`/folders/edit/${folder_id}`, {
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
                    set_modal_error_state(
                        editFolderModal,
                        data.message,
                        "edit"
                    );
                }
            });
    }
    // Delete
    const deleteModal = document.querySelector("#delete-confirmation-modal");
    const deleteButtons = document.querySelectorAll("button.delete");
    deleteButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setup_delete_modal(button.parentElement.parentElement);
            deleteModal.showModal();
        });
    });

    const deleteFolderCloseButton = deleteModal.querySelector(".modal-close");
    deleteFolderCloseButton.addEventListener("click", () => {
        ERROR_STATUS.delete = false;
        deleteModal.close();
    });

    function setup_delete_modal(folder_card) {
        const delete_message = deleteModal.querySelector(".delete-message");
        const folder_name = folder_card.querySelector(".name").textContent;
        const folder_id = folder_card.id;

        delete_message.innerHTML = `Are you sure you want to delete the folder 
                                    <i>${folder_name}</i> (id=${folder_id})?`;

        const deleteFolderButton = deleteModal.querySelector(".main-action");
        deleteFolderButton.addEventListener(
            "click",
            () => {
                post_delete_folder(folder_id);
            },
            { once: true }
        );
    }

    function post_delete_folder(folder_id) {
        fetch(`/folders/delete/${folder_id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success === true) {
                    window.location.reload();
                } else {
                    set_modal_error_state(deleteModal, data.message, "delete");
                }
            });
    }

    // Add files
    const addFilesButtons = document.querySelectorAll("button.add-files");
    addFilesButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const folder_id = button.parentElement.parentElement.id;
            post_add_files(folder_id);
        });
    });

    function post_add_files(folder_id) {
        fetch(`/folders/add_files/${folder_id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success === true) {
                    window.location.reload();
                } else {
                    alert("Something went wrong. Please check out the logs.");
                }
            });
    }

    // General Helper functions
    function set_modal_error_state(modal, message, type) {
        const modalMessage = modal.querySelector(".message");
        modalMessage.innerText = message;
        modal.querySelector("button.main-action").classList.add("error");
        ERROR_STATUS[type] = true;
    }

    function reset_modal(modal) {
        modal.querySelector("button.main-action").classList.remove("error");
        modal.querySelector(".message").innerText = "";
    }
})();
