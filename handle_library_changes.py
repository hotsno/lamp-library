def handle_library_changes(previous_library, new_library):
    removed_manga = previous_library.keys() - new_library.keys()
    added_manga = new_library.keys() - previous_library.keys()

    for manga in removed_manga:
        remove_manga(manga)

    for manga in added_manga:
        add_manga(manga)
    
    for manga in new_library:
        if manga in previous_library:
            added_cbz_files = list(set(new_library[manga]['cbz_files']) - set(previous_library[manga]['cbz_files']))
            removed_cbz_files = list(set(previous_library[manga]['cbz_files']) - set(new_library[manga]['cbz_files']))
            add_cbz_files(manga, added_cbz_files)
            remove_cbz_files(manga, removed_cbz_files)
        else:
            added_cbz_files = new_library[manga]['cbz_files']
            add_cbz_files(manga, list(added_cbz_files))

def remove_manga(manga):
    print(f"Removing manga: {manga}")

def add_manga(manga):
    print(f"Adding manga: {manga}")

def add_cbz_files(manga, cbz_files):
    if len(cbz_files) == 0:
        return
    print(f"Adding CBZ files: {cbz_files} to manga: {manga}")

def remove_cbz_files(manga, cbz_files):
    if len(cbz_files) == 0:
        return
    print(f"Removing CBZ files: {cbz_files} from manga: {manga}")