function calculateDiscount(price, isMember) {
    var memberRate = 0.15;
    var guestRate = 0.05;
    return isMember ? price * (1 - memberRate) : price * (1 - guestRate);
}
module.exports = { calculateDiscount };
