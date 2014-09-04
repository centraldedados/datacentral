var data = null;

$.ajax('/api.json')
    .done(function(response) {
        data = response;
    });

$('#search').on('change paste keyup', function() {
    var term = $(this).val();
    var results;
    $('.datasets > li').show();
    $(".notfound").hide();
    if (term.length >= 2) {
        $('#spinner').css('visibility', 'visible');
        results = _.map(search(term), function(result) {
            return '.dataset-' + result;
        });
        setTimeout(function() {
            $('#spinner').css('visibility', 'hidden');
        }, 1000);

        console.log(results);
        console.log(results.length);
        $(".datasets > li:not('" + results.toString() + "')").hide();
        if (results.length === 0) {
            $(".notfound").show();
        }
    }
});

function search(term) {
    if (!data) {
        console.error('Data not yet set');
        return;
    }

    var result =  _.filter(data, function(dataset) {
        return (dataset.title.toLowerCase().indexOf(term.toLowerCase()) > -1);
    });

    return _.pluck(result, 'name');
}