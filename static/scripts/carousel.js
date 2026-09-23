const carousel = document.querySelector('.car-container');
const images = document.querySelectorAll('.carousel-img');
const totalItems = images.length -3;
var width = 0
console.log("Carousel width:", width)
let index = 0;
var divisor = 4;

function getWidth() {
    var width = 0
    images.forEach(img => {
        width = width + img.clientWidth
        // console.log("current width:", width)
    });
    return width
}

function getWindowWith() {
    let width = document.documentElement.clientWidth;
    if (width < 780) {
        divisor = 1;
    } else {
        divisor = 4;
    }
    return width
}

function next() {
    index = (index + 1);
    updateCarousel();
}

window.setInterval(next, 8000);

document.querySelector('.next').addEventListener('click', () => {
    index = (index + 1)
    updateCarousel();
});

document.querySelector('.prev').addEventListener('click', () => {
    index = (index - 1)
    if(index < 1) {
        var viewWidth = getWindowWith()
        index = (width-viewWidth) / (viewWidth / divisor)
        // console.log("index: ", index)
    }
    updateCarousel();
});

function updateCarousel() {
    var viewWidth = getWindowWith()
    width = getWidth()

    // console.log("Window Width:", viewWidth)
    var newOffset = (viewWidth / divisor) * index
    if (newOffset > width-viewWidth) {
        newOffset= width-viewWidth+divisor
        index =-1
    }
    // console.log("New offset:", newOffset)
    carousel.style.transform = `translateX(${-newOffset}px)`;
}
