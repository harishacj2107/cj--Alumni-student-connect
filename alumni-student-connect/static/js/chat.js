function startChat(receiverId) {
    function fetchMessages() {
        $.ajax({
            url: '/chat/messages/' + receiverId,
            method: 'GET',
            success: function(data) {
                $('#chat-box').empty();
                data.forEach(function(msg) {
                    var alignment = msg[1] == {{ session.get('student_id') or session.get('alumni_id') }} ? 'text-end' : 'text-start';
                    $('#chat-box').append(
                        '<div class="' + alignment + '"><p><strong>' + msg[1] + ':</strong> ' + msg[3] + ' <small>' + msg[4] + '</small></p></div>'
                    );
                });
                $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
            }
        });
    }
    fetchMessages();
    setInterval(fetchMessages, 5000); // Poll every 5 seconds
}