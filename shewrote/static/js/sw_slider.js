
(function() {
    getSliderElements = function(prefix) {
        return [
            document.getElementById(prefix + "_slider"),
            document.getElementById(prefix + "_start"),
            document.getElementById(prefix + "_end")
        ];
    };

    enableSlider = function(prefix) {
        const [slider, start_input, end_input] = getSliderElements(prefix);
        slider.noUiSlider.enable();
        start_input.disabled = false;
        end_input.disabled = false;
    };

    disableSlider = function(prefix) {
        const [slider, start_input, end_input] = getSliderElements(prefix);
        slider.noUiSlider.disable();
        start_input.disabled = true;
        end_input.disabled = true;
    };

    setSliderVisibility = function(checkbox, prefix) {
        if (checkbox.checked == true) {
            enableSlider(prefix);
        } else {
            disableSlider(prefix);
        }
    };

    addChangeListener = function(checkbox, prefix) {
        checkbox.addEventListener('change', function() {
            setSliderVisibility(checkbox, prefix);
        });
    };

    registerSlider = function(prefix) {
        checkbox = document.querySelector("#"+prefix+"_checkbox");
        addChangeListener(checkbox, prefix);
        setSliderVisibility(checkbox, prefix);
    };
})();