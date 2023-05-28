myScope = {
    status: false,
    checkStatus: function () {
        if (this.status) {
            console.log("Status is true");
        } else {
            console.log("Status is false");
        }
    },
    setStatus: function (status) {
        this.status = status;
    },
};

(function () {
    var variable = null;
    function printIfstatus() {
        if (myScope.status) {
            console.log("opa");
        } else {
            console.log("deu ruim");
        }
    }

    printIfstatus();
})();
