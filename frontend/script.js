const API_URL = "http://127.0.0.1:8000";

async function fetchNotes(tag = "") {
    let url = `${API_URL}/notes`;

    if (tag) {
        url += `?tag=${encodeURIComponent(tag)}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to fetch notes: ${response.status}`);
    }

    return await response.json();
}

async function createNote(noteData) {

    const response = await fetch(`${API_URL}/notes`, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(noteData)
    });

    if (!response.ok) {

        let errorMessage = "Failed to create note";

        try {
            const errorData = await response.json();

            if (errorData.detail) {
                errorMessage = errorData.detail;
            }

        } catch (error) {
            console.error("Could not read API error:", error);
        }

        throw new Error(errorMessage);
    }
    return await response.json();

}

async function deleteNote(noteId, token) {

    const response = await fetch(
        `${API_URL}/notes/${noteId}`,
        {
            method: "DELETE",

            headers: {
                "x-token": token
            }
        }
    );

    if (!response.ok) {

        let errorMessage = "Failed to delete note";

        try {
            const errorData = await response.json();

            if (errorData.detail) {
                errorMessage = errorData.detail;
            }

        } catch (error) {
            console.error("Could not read API error:", error);
        }

        throw new Error(errorMessage);
    }
    return true;
}

// =====================================================
// DOM ELEMENTS
// =====================================================

const notesContainer =
    document.getElementById("notesContainer");

const notesLoading =
    document.getElementById("notesLoading");

const notesError =
    document.getElementById("notesError");

const noteForm =
    document.getElementById("noteForm");

const formError =
    document.getElementById("formError");

const searchInput =
    document.getElementById("searchInput");

const searchStatus =
    document.getElementById("searchStatus");

const categoryTreeContainer =
    document.getElementById("categoryTree");

// Keep the latest notes in memory.
// Search can filter this data without another API request.
let allNotes = [];

// Used for debounced search.
let searchTimeout;

// =====================================================
// DYNAMIC NOTE RENDERING
// =====================================================

function renderNotes(notes) {


    notesContainer.innerHTML = "";

    if (notes.length === 0) {

        const emptyMessage =
            document.createElement("p");

        emptyMessage.textContent = "No notes found.";

        notesContainer.appendChild(emptyMessage);

        return;
    }


    notes.forEach(function (note) {

        // Main note card
        const noteCard =
            document.createElement("article");

        noteCard.className = "note";


        // Title
        const title =
            document.createElement("h3");

        title.textContent = note.title;

        noteCard.appendChild(title);


        // Content
        const content =
            document.createElement("p");

        content.textContent = note.content;

        noteCard.appendChild(content);


        // Tag
        const tag =
            document.createElement("span");

        tag.className = "note-tag";

        tag.textContent =
            `Tag: ${note.tag || "No tag"} `;

        noteCard.appendChild(tag);


        // AI suggestion from Part 3
        if (note.ai_suggestion) {

            const suggestion =
                document.createElement("div");

            suggestion.className =
                "ai-suggestion";


            const suggestionTitle =
                document.createElement("strong");

            suggestionTitle.textContent =
                "AI Suggestion";

            suggestion.appendChild(suggestionTitle);


            const suggestionText =
                document.createElement("span");

            suggestionText.textContent =
                note.ai_suggestion;

            suggestion.appendChild(suggestionText);


            noteCard.appendChild(suggestion);
        }


        // Delete button
        const deleteButton =
            document.createElement("button");

        deleteButton.className =
            "delete-button";

        deleteButton.textContent =
            "Delete";


        // Store note ID on the button
        deleteButton.dataset.noteId =
            note.id;


        // Delete click event
        deleteButton.addEventListener(
            "click",
            async function () {

                await handleDeleteNote(
                    note.id,
                    noteCard
                );
            }
        );


        noteCard.appendChild(deleteButton);


        // Add card to the page
        notesContainer.appendChild(noteCard);
    });


}

// =====================================================
// LOAD NOTES
// =====================================================

async function loadNotes() {


    notesLoading.hidden = false;
    notesError.hidden = true;

    try {

        const notes =
            await fetchNotes();

        allNotes = notes;

        renderNotes(allNotes);

    } catch (error) {

        console.error(
            "Error loading notes:",
            error
        );

        notesError.textContent =
            "Unable to load notes. Please check that the backend is running.";

        notesError.hidden = false;

    } finally {

        notesLoading.hidden = true;
    }


}

// =====================================================
// ADD NOTE
// =====================================================

noteForm.addEventListener(
    "submit",
    async function (event) {


        event.preventDefault();


        // Clear previous validation message
        formError.textContent = "";
        formError.hidden = true;


        const titleInput =
            document.getElementById("title");

        const contentInput =
            document.getElementById("content");

        const tagInput =
            document.getElementById("tag");

        const ownerInput =
            document.getElementById("owner_id");


        const title =
            titleInput.value.trim();

        const content =
            contentInput.value.trim();

        const tag =
            tagInput.value.trim();

        const ownerId =
            Number(ownerInput.value);


        // Client-side validation
        if (!title || !content) {

            formError.textContent =
                "Title and content are required.";

            formError.hidden = false;

            return;
        }


        if (!ownerId) {

            formError.textContent =
                "Owner ID is required.";

            formError.hidden = false;

            return;
        }


        const noteData = {
            title: title,
            content: content,
            tag: tag,
            owner_id: ownerId
        };


        try {

            const newNote =
                await createNote(noteData);


            // Add returned note to our local data
            allNotes.push(newNote);


            // Clear search so new note is visible
            searchInput.value = "";

            searchStatus.textContent = "";


            // Render the returned note without
            // reloading the whole page
            renderNotes(allNotes);


            // Reset form
            noteForm.reset();


        } catch (error) {

            console.error(
                "Error creating note:",
                error
            );

            formError.textContent =
                error.message;

            formError.hidden = false;
        }
    }


);

// =====================================================
// DELETE NOTE
// =====================================================

async function handleDeleteNote(noteId, noteCard) {

    const token = window.prompt("Enter delete token:");

    if (!token) {
        return;
    }

    try {

        await deleteNote(noteId, token);

        // Remove the note from the page
        noteCard.remove();

        // Remove the note from local data
        allNotes = allNotes.filter(function (note) {
            return note.id !== noteId;
        });

        searchStatus.textContent = "Note deleted successfully.";

    } catch (error) {

        console.error("Error deleting note:", error);

        notesError.textContent = error.message;
        notesError.hidden = false;
    }
}

// =====================================================
// DEBOUNCED SEARCH
// =====================================================

searchInput.addEventListener(
    "input",
    function () {


        clearTimeout(searchTimeout);


        searchTimeout = setTimeout(
            function () {

                const searchValue =
                    searchInput.value
                        .trim()
                        .toLowerCase();


                // Empty search = show everything
                if (!searchValue) {

                    renderNotes(allNotes);

                    searchStatus.textContent = "";

                    return;
                }


                /*
                    Plain client-side search.
        
                    It matches:
                    - title
                    - tag
                */

                const matchingNotes =
                    allNotes.filter(
                        function (note) {

                            const title =
                                (note.title || "")
                                    .toLowerCase();

                            const tag =
                                (note.tag || "")
                                    .toLowerCase();


                            return (
                                title.includes(searchValue) ||
                                tag.includes(searchValue)
                            );
                        }
                    );


                renderNotes(matchingNotes);


                searchStatus.textContent =
                    `${matchingNotes.length} note(s) found.`;

            },
            400
        );
    }


);

// =====================================================
// RECURSIVE CATEGORY TREE
// =====================================================

const CATEGORY_TREE = {
    name: "All Tags",


    children: [

        {
            name: "Work",

            children: [

                {
                    name: "Standups",
                    children: []
                },

                {
                    name: "Retros",
                    children: []
                }
            ]
        },


        {
            name: "Personal",

            children: [

                {
                    name: "Health",

                    children: [

                        {
                            name: "Fitness",
                            children: []
                        }
                    ]
                },

                {
                    name: "Recipes",
                    children: []
                }
            ]
        },


        {
            name: "Travel",
            children: []
        }
    ]


};
function renderCategoryTree(node, container) {
    const item = document.createElement("div");
    item.classList.add("category-item");

    const row = document.createElement("div");
    row.classList.add("category-row");

    const toggle = document.createElement("button");

    toggle.textContent =
        node.children && node.children.length > 0 ? "−" : "•";

    const name = document.createElement("span");
    name.textContent = node.name;

    row.appendChild(toggle);
    row.appendChild(name);
    item.appendChild(row);

    const childrenContainer = document.createElement("div");
    childrenContainer.classList.add("category-children");

    if (node.children && node.children.length > 0) {

        node.children.forEach(function (child) {
            renderCategoryTree(child, childrenContainer);
        });

        toggle.addEventListener("click", function () {
            const isHidden = childrenContainer.hidden;

            childrenContainer.hidden = !isHidden;
            toggle.textContent = isHidden ? "+" : "−";
        });

    } else {
        toggle.disabled = true;
    }

    container.appendChild(item);
}

const categoryContainer =
    document.getElementById("category-tree");

renderCategoryTree(CATEGORY_TREE, categoryContainer);
// Recursive function
function createCategoryNode(category) {


    const listItem =
        document.createElement("li");

    listItem.className =
        "category-node";


    const categoryName =
        document.createElement("span");

    categoryName.className =
        "category-name";

    categoryName.textContent =
        category.name;

    listItem.appendChild(categoryName);


    // If children exist, recursively create them
    if (
        category.children &&
        category.children.length > 0
    ) {

        const childList =
            document.createElement("ul");

        childList.className =
            "category-children";


        category.children.forEach(
            function (child) {

                const childNode =
                    createCategoryNode(child);

                childList.appendChild(childNode);
            }
        );


        listItem.appendChild(childList);
    }


    return listItem;


}

// Render category tree
function renderCategoryTree(tree) {


    categoryTreeContainer.innerHTML = "";


    const rootList =
        document.createElement("ul");


    const rootNode =
        createCategoryNode(tree);


    rootList.appendChild(rootNode);


    categoryTreeContainer.appendChild(rootList);


}

// =====================================================
// PAGE LOAD
// =====================================================

async function initializeApp() {


    renderCategoryTree(
        CATEGORY_TREE
    );

    await loadNotes();


}

initializeApp();
