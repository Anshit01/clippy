// document.getElementById('textarea').innerHTML = "Helloafsdf"
var curTime = getCurrentTime()
var lastUpdateTime = getPreciseCurrentTime()
var textareaText = ''

var connectionId = ''
var userId = ''
var user_name = ''
var user_email = ''
var photoURL = ''

var clipId = ''
var clipName = 'Untitled'


// Firebase configuration
var firebaseConfig = {
    apiKey: "AIzaSyBlkHqdolHzPDu7lYuAmPv7K1ImaPAr9Lk",
    authDomain: "clippy-3da02.firebaseapp.com",
    databaseURL: "https://clippy-3da02.firebaseio.com",
    projectId: "clippy-3da02",
    storageBucket: "clippy-3da02.appspot.com",
    messagingSenderId: "476084889049",
    appId: "1:476084889049:web:84211cd1769b7ef39225c8"
  };
// Initialize Firebase
firebase.initializeApp(firebaseConfig);

var provider = new firebase.auth.GoogleAuthProvider();

var socket
$(document).ready( () => {

    var textareaTopOffset = $('#textarea').offset().top
    $('#textarea').outerHeight($(document).height() - textareaTopOffset)

    $('#textarea').focus();

    $(window).on('resize', () => {
        $('#textarea').outerHeight($(document).height() - $('#textarea').offset().top)
    })

    $('#new-btn').click(() => {
        var clipsArray = []
        $('.recent-clip').each(function() {
            clipsArray.push($(this).html())
        })
        var newClipName = 'Untitled'
        if(clipsArray.indexOf(newClipName) != -1){
            var ind = 1
            while(clipsArray.indexOf(newClipName + '-' + ind) != -1){
                ind++
            }
            newClipName += '-' + ind
        }
        showLoading()
        socket.emit('new_clip', userId, newClipName, '', clipId)
    })

    $('#delete-btn').click(function() {
        showLoading()
        socket.emit('delete_clip', connectionId, clipId)
    })

    $('#open-btn').click(function() {
        $('#file-selector').click()
    })

    $('#file-selector').change(function(event) {
        var file = event.target.files[0]
        var fileName = file.name
        var fileSize = file.size
        if(fileSize <= 102400){
            var fileReader = new FileReader()
            fileReader.readAsText(file)
            fileReader.addEventListener('load', function(e) {
                var fileContent = e.target.result
                socket.emit('new_clip', userId, fileName, fileContent, clipId)
                showLoading()
            })
        }else {
            alert('File size limit of 100KB exceded.')
        }
    })

    $('.recent-clip').on('click', function() {
        var selectedClipId = $(this).attr('id')
        showLoading()
        socket.emit('get_clip', userId, selectedClipId)
    })

    $('')

    $('#login-btn, #google-signin').click(() => {
        if($('#login-btn').html() == 'Sign in'){
            login()
        }else{
            logout()
        }
    })

    socket = io.connect('/')
    socket.on('connect', () => {
        socket.send('User has connected!')
    })

    socket.on('connect_response', (con_id) => {
        connectionId = con_id
        console.log('connected with connectionId: ' + connectionId)
    })

    socket.on('login_response', (err, id, name, email, clipList, photo_URL, recentClipId, clip_name, clip_data) => {
        console.log('logged in finally')
        if(err){
            console.error('error in login to backend')
            console.error(err)
        }else{
            userId = id
            userName = name
            userEmail = email
            photoURL = photo_URL
            $('#profile-img').attr('src', photoURL)
            $('#profile-img-lg').attr('src', photoURL)
            $('#user-name').text(name)
            $('#user-email').text(email)
            $('#login-btn').html('Logout')
            
            //filling recent clips drop down list
            var clipLength = Object.keys(clipList).length
            var i = 1
            var content = ''
            for(clip_id in clipList){
                content += '<a id="' + clip_id + '" class="dropdown-item recent-clip">' + clipList[clip_id] + '</a>'
                // if(i < clipLength){
                //     content += '<div class="dropdown-divider"></div>'
                // }
                i++
            }
            $('#recent-clip-list').html(content)
            $('.recent-clip').on('click', function() {
                var selectedClipId = $(this).attr('id')
                showLoading()
                socket.emit('get_clip', userId, selectedClipId)
            })
            setClip(recentClipId, clip_name, clip_data)
            hideLoading()
            showLandingPage(false)
        }
    })

    socket.on('message', (msg) => {
        console.log('message: ' + msg)
    })

    socket.on('test_response', (err, json) => {
        console.log(err);
        console.log(json)
    })

    socket.on('text_response', (con_id, text, clip_id, clip_name, timestamp) => {
        if(connectionId != con_id && clip_id == clipId && timestamp > lastUpdateTime){
            textareaText = text
            $('#textarea').val(text)
        }
        $('#' + clip_id).text(clip_name)
    })

    socket.on('clip_response', (err, clip_id, clip_name, clip_data) => {
        if(err){
            console.error(err)
        }else{
            hideLoading()
            setClip(clip_id, clip_name, clip_data)
        }
    })

    socket.on('new_clip_response', (err, newClipId, newClipName, clip_data, old_clip_id) => {
        if(err){
            console.error(err)
        }else{
            if(clipId == old_clip_id){
                setClip(newClipId, newClipName, clip_data)
            }
            $('#recent-clip-list').html(
                '<a id="' + clipId + '" class="dropdown-item recent-clip">' + clipName + '</a>'
                // + '<div class="dropdown-divider"></div>'
                + $('#recent-clip-list').html()
            )
            $('.recent-clip').on('click', function() {
                var selectedClipId = $(this).attr('id')
                showLoading()
                socket.emit('get_clip', userId, selectedClipId)
            })
        }
        hideLoading()
    })

    socket.on('delete_clip_response', (connection_id, old_clip_id, new_clip_id) => {
        console.log('Deleted clip: ' + old_clip_id)
        $('#' + old_clip_id).remove()
        if(connection_id == connectionId){
            if(new_clip_id == ''){
                $('#new-btn').trigger('click')
            }
        }
        if(old_clip_id == clipId && new_clip_id != ''){
            socket.emit('get_clip', userId, new_clip_id)
        }
    })

    socket.on('logout_response', (err, res) => {
        if(err){
            console.error(err)
        }else{
            console.log(res)
            userId = ''
            user_name = ''
            user_email = ''
            photoURL = ''
            clipId = ''
            clipName = 'Untitled'
            $('#login-btn').html('Sign in')
            $('#profile-img').removeAttr('src')
            $('#profile-img-lg').removeAttr('src')
            showLandingPage(true)
        }
    })

    // $('#textarea').on('input', () => {
    //     text = $('#textarea').val()
    //     socket.send(text)
    // })
    
    setInterval(() => {
        var curText = $('#textarea').val()
        var curName = $('#clip-name').val()
        if(userId != '' && (curText != textareaText || curName != clipName)) {
            socket.emit('update_text', connectionId, userId, clipId, curName, curText, getPreciseCurrentTime())
            textareaText = curText
            clipName = curName
        }
    }, 1000)

})

function login() {
    firebase.auth().signInWithPopup(provider).then(function(result) {
        var name = result.user.displayName
        var email = result.user.email
        var uid = result.user.uid
        photoURL = result.user.photoURL
        socket.emit('login', name, email, uid, photoURL)
        console.log('logged in')
        showLandingPage(false)
        showLoading()
    }).catch(function(error) {
        var errorCode = error.code;
        var errorMessage = error.message;
        // The email of the user's account used.
        var email = error.email;
        // The firebase.auth.AuthCredential type that was used.
        var credential = error.credential;
        console.log('error in login')
    });
}

function logout() {
    socket.emit('logout')
    firebase.auth().signOut().then(function() {
        console.log('Signed out from firebase')
    }).catch(function(error) {
        console.error('Sign out error')
    });
}

function showLandingPage(show) {
    if(show){
        $('.landing-page').fadeIn()
        $('.whole').fadeOut()
    }else{
        $('.whole').fadeIn()
        $('.landing-page').fadeOut()
    }
}

function getCurrentTime() {
    return Math.floor(new Date().getTime() / 1000)
}

function getPreciseCurrentTime() {
    return new Date().getTime()
}

function showLoading() {
    $('#loader').removeClass('hidden')
}

function hideLoading() {
    $('#loader').addClass('hidden')

    $('#textarea').focus();
}

function setClip(clip_id, clip_name, clip_data) {
    clipName = clip_name
    clipId = clip_id
    $('#clip-name').val(clip_name)
    $('#textarea').val(clip_data)
}
