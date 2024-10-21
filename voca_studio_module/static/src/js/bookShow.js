/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.bookShow = publicWidget.Widget.extend({
    /* Extending widget and creating book show */
    selector: '.book_show',
    events: {
        'change #choose_date' : 'CheckShows',
    },
CheckShows: function (ev) {
    const dateInputs = this.$el.find('input[name="show_date[]"]');
    const currentDateTime = new Date();
    let allValid = true;
    let dateTimeDict = {};  // Dictionary to store all date-time inputs

    // Loop through each date-time input and validate it
    dateInputs.each(function(index, input) {
        const selectedDateTimeString = input.value;  // Get the value as a string
        const selectedDateTime = new Date(selectedDateTimeString);  // Convert the string into a Date object

        console.info("Selected Date and Time:", selectedDateTime);

        if (selectedDateTime < currentDateTime) {
            input.value = '';  // Clear the invalid date input
            allValid = false;  // Mark as invalid
            $(input).closest('.date-slot-group').find('.error_box').text('Please select a date in the future!').show();
        } else {
            $(input).closest('.date-slot-group').find('.error_box').hide();
            // Add valid date-time to the dictionary (index is used as a key)
            dateTimeDict[`date_time_${index}`] = selectedDateTimeString;
        }
    });

    // If all dates are valid, store them in a hidden field for the form submission
    if (allValid) {
        this.$el.find('#error_box').hide();

        // Convert dictionary to a JSON string and store it in a hidden input field
        const hiddenInput = this.$el.find('input[name="date_time_dict"]');
        hiddenInput.val(JSON.stringify(dateTimeDict));  // Store the dictionary as a JSON string

        console.info("Final Date-Time Dictionary:", dateTimeDict);
    }
},
    checkShowsOnDate: function (ev, date, movieId) {
        /* Function for checking shows on the selected date. */
        const formattedDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000))
                          .toISOString().split('T')[0];
        return jsonrpc("/web/dataset/call_kw", {
            model: 'movie.movie',
            method: 'check_shows_on_date',
            args: [formattedDate,movieId],
            kwargs: {}
        }).then((result) => {
            if (!result){
                ev.currentTarget.value = ''
                this.$el.find('#error_box').text('There is no shows on the selected date!!')
                this.$el.find('#error_box').show()
                this.$el.find('.tickets_section').hide()
            }
            else{
                this.$el.find('.tickets_section').show()
            }
        })
    },



});
