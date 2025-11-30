console.log("Tinko SDK Loaded");

window.Tinko = {
    init: function (config) {
        console.log("Tinko initialized with config:", config);
        this.config = config;
    },
    recover: function (transactionRef) {
        console.log("Initiating recovery for:", transactionRef);
        // Logic to open recovery modal or redirect
        const baseUrl = this.config.baseUrl || "https://tinko.in";
        window.location.href = `${baseUrl}/pay/retry/${transactionRef}`;
    }
};
