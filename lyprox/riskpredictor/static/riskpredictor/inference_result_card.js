/**
 * Toggle the collapsible div
 */
function toggleCollapsible(id) {
    var collapsibleElement = $(`#collapsible-${id}`);

    if (collapsibleElement.hasClass('is-hidden')) {
        collapsibleElement.removeClass('is-hidden');
    } else {
        collapsibleElement.addClass('is-hidden');
    };
};
