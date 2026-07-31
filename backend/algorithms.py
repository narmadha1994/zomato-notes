def insertion_sort_by_key(items: list[dict], key: str) -> list[dict]:
    result = items.copy()

    for i in range(1, len(result)):
        current = result[i]
        j = i - 1

        while j >= 0 and result[j][key] < current[key]:
            result[j + 1] = result[j]
            j -= 1

        result[j + 1] = current

    return result


def binary_search_iterative(
    sorted_titles: list[str],
    target: str
) -> int:
    start = 0
    end = len(sorted_titles) - 1

    while start <= end:
        mid = start + (end - start) // 2

        if sorted_titles[mid] == target:
            return mid

        if sorted_titles[mid] < target:
            start = mid + 1
        else:
            end = mid - 1

    return -1


def binary_search_recursive(
    sorted_titles: list[str],
    target: str,
    start: int,
    end: int
) -> int:

    if start > end:
        return -1

    mid = start + (end - start) // 2

    if sorted_titles[mid] == target:
        return mid

    if sorted_titles[mid] < target:
        return binary_search_recursive(
            sorted_titles,
            target,
            mid + 1,
            end
        )

    return binary_search_recursive(
        sorted_titles,
        target,
        start,
        mid - 1
    )


def linear_search(
    items: list[dict],
    key: str,
    value
) -> dict | None:

    found = False
    result = None
    index = 0

    while index < len(items) and not found:

        if items[index].get(key) == value:
            result = items[index]
            found = True

        index += 1

    return result