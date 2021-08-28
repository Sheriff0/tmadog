package dog;

import java.lang.Throwable;
import java.io.IOException;

class AuthError extends Exception {
    /** Serialization ID */
    private static final long serialVersionUID = 0;

    /**
     *
     * @param message
     *            Detail about the reason for the exception.
     */
    public AuthError(final String message) {
        super(message);
    }

    /**
     * 
     * @param message
     *            Detail about the reason for the exception.
     * @param cause
     *            The cause.
     */
    public AuthError(final String message, final Throwable cause) {
        super(message, cause);
    }

    /**
     * 
     * @param cause
     *            The cause.
     */
    public AuthError(final Throwable cause) {
        super(cause.getMessage(), cause);
    }

}

class NoFileNoCreate extends IOException {
    /** Serialization ID */
    private static final long serialVersionUID = 0;

    /**
     *
     * @param message
     *            Detail about the reason for the exception.
     */
    public NoFileNoCreate(final String message) {
        super(message);
    }

    /**
     * 
     * @param message
     *            Detail about the reason for the exception.
     * @param cause
     *            The cause.
     */
    public NoFileNoCreate(final String message, final Throwable cause) {
        super(message, cause);
    }

    /**
     * 
     * @param cause
     *            The cause.
     */
    public NoFileNoCreate(final Throwable cause) {
        super(cause.getMessage(), cause);
    }

}

class NoDirNoRead extends RuntimeException {
    /** Serialization ID */
    private static final long serialVersionUID = 0;

    /**
     *
     * @param message
     *            Detail about the reason for the exception.
     */
    public NoDirNoRead(final String message) {
        super(message);
    }

    /**
     * 
     * @param message
     *            Detail about the reason for the exception.
     * @param cause
     *            The cause.
     */
    public NoDirNoRead(final String message, final Throwable cause) {
        super(message, cause);
    }

    /**
     * 
     * @param cause
     *            The cause.
     */
    public NoDirNoRead(final Throwable cause) {
        super(cause.getMessage(), cause);
    }

}



class
Errno extends Exception
{
    static Exception errno;
}
