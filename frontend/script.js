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

async function fetchRankedNotes(keyword, sortBy) {
    let url;

    if (sortBy === "date") {
        url = `${API_URL}/notes/search?sort_by=date`;
    } else {
        url = `${API_URL}/notes/search?keyword=${encodeURIComponent(keyword)}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Ranking search failed: ${response.status}`);
    }

    return await response.json();
}

async function lookupTitle(title, algo) {

    const response = await fetch(
        `${API_URL}/notes/lookup?title=${encodeURIComponent(title)}&algo=${algo}`
    );

    if (!response.ok) {
        throw new Error("Lookup failed");
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



// =====================================================
// DOM ELEMENTS
// =====================================================

const notesContainer = document.getElementById("notesContainer");
const notesLoading = document.getElementById("notesLoading");
const notesError = document.getElementById("notesError");
const noteForm = document.getElementById("noteForm");
const formError = document.getElementById("formError");
const searchInput = document.getElementById("searchInput");
const searchStatus = document.getElementById("searchStatus");
const sortMode = document.getElementById("sortMode");
const titleLookup = document.getElementById("titleLookup");
const lookupAlgo = document.getElementById("lookupAlgo");
const lookupButton = document.getElementById("lookupButton");
const categoryTreeContainer = document.getElementById("categoryTree");
const quickTagButtons = document.querySelectorAll(".quick-tag-button");
const quickTagStatus = document.getElementById("quickTagStatus");

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
        const noteCard = document.createElement("article");
        noteCard.className = "note";

        // Store the backend note ID on the card
        noteCard.dataset.noteId = note.id;

        // Title
        const title = document.createElement("h3");
        title.textContent = note.title;
        noteCard.appendChild(title);

        // Content
        const content = document.createElement("p");
        content.textContent = note.content;
        noteCard.appendChild(content);


        // Tag
        const tag = document.createElement("span");
        tag.className = "note-tag";
        tag.textContent =
            `Tag: ${note.tag || "No tag"} `;
        noteCard.appendChild(tag);


        // AI suggestion from Part 3
        if (note.ai_suggestion) {

            const suggestion = document.createElement("div");
            suggestion.className = "ai-suggestion";

            const heading = document.createElement("strong");
            heading.textContent = "AI Suggests";
            suggestion.appendChild(heading);

            // Summary
            const summary = document.createElement("p");
            summary.textContent =
                "Summary: " + note.ai_suggestion.summary;
            suggestion.appendChild(summary);

            // Tags
            const tags = document.createElement("p");
            tags.textContent =
                "Tags: " + note.ai_suggestion.tags.join(", ");
            suggestion.appendChild(tags);

            // Apply button
            const applyButton = document.createElement("button");
            applyButton.textContent = "Apply as tag";

            applyButton.addEventListener("click", async function () {

                const firstTag = note.ai_suggestion.tags[0];

                const response = await fetch(
                    `http://127.0.0.1:8000/notes/${note.id}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            title: note.title,
                            content: note.content,
                            tag: firstTag
                        })
                    }
                );

                if (response.ok) {
                    loadNotes();
                }
                else {
                    alert("Unable to update tag.");
                }

            });

            suggestion.appendChild(applyButton);
            noteCard.appendChild(suggestion);
        }

        const smartSearchButton = document.getElementById("smart-search-button");

        smartSearchButton.addEventListener(
            "click",
            smartSearch
        );

        async function smartSearch() {

            const query =
                document.getElementById(
                    "smart-search-input"
                ).value;

            const response =
                await fetch(
                    `http://127.0.0.1:8000/notes/smart-search?q=${encodeURIComponent(query)}`
                );

            const results =
                await response.json();

            displaySmartResults(results);

        }

        function displaySmartResults(results) {

            const container =
                document.getElementById(
                    "smart-search-results"
                );

            container.replaceChildren();

            results.forEach(function (note) {

                const card =
                    createSmartSearchCard(note);

                container.appendChild(card);

            });

        }

        function createSmartSearchCard(note) {

            const card =
                document.createElement("article");

            card.className =
                "smart-search-card";

            const title =
                document.createElement("h3");

            title.textContent =
                note.title;

            card.appendChild(title);

            const content =
                document.createElement("p");

            content.textContent =
                note.content;

            card.appendChild(content);

            const score =
                document.createElement("p");

            score.className =
                "similarity-score";

            score.textContent =
                "Similarity Score: " +
                note.score;

            card.appendChild(score);

            return card;

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


        const titleInput = document.getElementById("title");
        const contentInput = document.getElementById("content");
        const tagInput = document.getElementById("tag");
        const ownerInput = document.getElementById("owner_id");
        const title = titleInput.value.trim();
        const content = contentInput.value.trim();
        const tag = tagInput.value.trim();
        const ownerId = Number(ownerInput.value);

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

sortMode.addEventListener("change", async function () {

    const keyword =
        searchInput.value.trim();

    const selectedMode =
        sortMode.value;

    try {

        if (selectedMode === "relevance" && !keyword) {
            searchStatus.textContent =
                "Enter a keyword to search by relevance.";
            return;
        }

        searchStatus.textContent =
            "Searching...";

        const results =
            await fetchRankedNotes(
                keyword,
                selectedMode
            );

        renderNotes(results);

        searchStatus.textContent =
            `${results.length} result(s) found.`;

    } catch (error) {

        console.error(
            "Ranking search error:",
            error
        );

        searchStatus.textContent =
            "Unable to perform ranked search.";
    }
});


// =====================================================
// QUICK TAG JUMP - LINEAR SEARCH
// =====================================================

async function quickFindTag(tag) {

    quickTagStatus.textContent =
        `Finding first "${tag}" note...`;

    try {

        const response = await fetch(
            `${API_URL}/notes/quick-find?tag=${encodeURIComponent(tag)}`
        );

        if (!response.ok) {
            throw new Error(
                `Quick tag search failed: ${response.status}`
            );
        }

        const result = await response.json();

        // No matching note
        if (!result.id) {

            quickTagStatus.textContent =
                `No note found with tag "${tag}".`;

            return;
        }

        quickTagStatus.textContent =
            `Found: ${result.title}`;

        // Make sure the returned note is visible
        renderNotes(allNotes);

        // Find the matching note card
        const noteCard =
            notesContainer.querySelector(
                `[data-note-id="${result.id}"]`
            );

        if (noteCard) {

            // Scroll to the note
            noteCard.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

            // Highlight the note
            noteCard.classList.add("quick-find-highlight");

            // Remove highlight after 2 seconds
            setTimeout(function () {
                noteCard.classList.remove(
                    "quick-find-highlight"
                );
            }, 2000);
        }

    } catch (error) {

        console.error(
            "Quick tag search error:",
            error
        );

        quickTagStatus.textContent =
            "Unable to perform quick tag search.";
    }
}


// Attach click events to all Quick Tag buttons
quickTagButtons.forEach(function (button) {

    button.addEventListener(
        "click",
        function () {

            const tag =
                button.dataset.tag;

            quickFindTag(tag);
        }
    );

});

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

function renderCategoryTree(node, parentElement) {
    const item = document.createElement("div");
    item.className = "category-item";

    const row = document.createElement("div");
    row.className = "category-row";

    const toggleButton = document.createElement("button");
    toggleButton.type = "button";

    const hasChildren =
        node.children && node.children.length > 0;

    toggleButton.textContent = hasChildren ? "−" : "•";

    const name = document.createElement("span");
    name.textContent = node.name;

    row.appendChild(toggleButton);
    row.appendChild(name);

    item.appendChild(row);
    parentElement.appendChild(item);

    if (hasChildren) {
        const childrenContainer = document.createElement("div");
        childrenContainer.className = "category-children";

        node.children.forEach(function (child) {
            renderCategoryTree(child, childrenContainer);
        });

        item.appendChild(childrenContainer);

        toggleButton.addEventListener("click", function () {
            childrenContainer.hidden =
                !childrenContainer.hidden;

            toggleButton.textContent =
                childrenContainer.hidden ? "+" : "−";
        });
    } else {
        toggleButton.disabled = true;
    }
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
// PAGE LOAD
// =====================================================

async function initializeApp() {

    categoryTreeContainer.innerHTML = "";

    renderCategoryTree(
        CATEGORY_TREE,
        categoryTreeContainer
    );

    await loadNotes();
}
initializeApp();